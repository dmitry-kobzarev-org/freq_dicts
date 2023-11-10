import os
import pandas as pd
from dk_google.cloud.iam import get_credentials
from dk_google.helpers import if_exist_replace
from google.cloud import firestore
from google.cloud.exceptions import NotFound, Conflict
from custom_lib.helpers import get_file_sha256
from dk_google import get_file_path
from dk_google.helpers import validate_param_in_allowed_list
import nltk
from nltk.corpus import wordnet
import re
from collections import Counter
from datetime import datetime as dt

nltk.download('punkt', quiet = True)

class FirestoreClient:
    
    def __init__(self, database):
        self.project_id = os.getenv('PROJECT_ID')
        self.cred_type = os.getenv('CRED_TYPE')
        self.creds = get_credentials(self.cred_type)
        self.client = firestore.Client(project = self.project_id, database = database,
                                      credentials = self.creds)
        self.database = database
        self.info_prefix = f'{self.project_id}, {self.database}: '
        self.LIMIT_CATALOG_DISPLAY_COLLECTION_ITEMS = 30
        
    def delete_collection(self, name):
        docs = self.list_documents(collection = name)
        for doc in docs:
            self.delete_document(doc)
        print(f'{self.info_prefix} collection "{name}" is deleted')

    def get_document(self, name, return_ref = False):
        doc_ref = self.client.document(name)
        if return_ref:
            return doc_ref
        doc = doc_ref.get()
        if not doc.exists:
            raise NotFound(f'{self.info_prefix}document "{name}" doesnt exist!')
        return doc.to_dict()

    def list_documents(self, collection, shortly = True):
        ls = [i for i in self.client.collection(collection).list_documents() if i.get().exists]
        if shortly:
            ls = [i.path for i in ls]
        return ls
    
    def delete_document(self, name):
        self.client.document(name).delete()
        print(f'{self.info_prefix}: document "{name}" is deleted')

    @if_exist_replace('document', False)
    def create_document(self, name = False, data = {}, if_exist_replace = False):
        self.client.document(name).set(data)
        print(f'{self.info_prefix}: document "{name}" is created')
    
    def update_document(self, name, data):
        self.client.document(name).update(data);
        print(f'{self.info_prefix}: document "{name}" is updated')

    def get_catalog(self, path = ''):
        if path == '':
            res = [{'type': 'collection', 'name': i.id} for i in self.client.collections()]
        else:
            path_len = len(path.split('/'))
            if path_len % 2 == 0:
                lm = self.LIMIT_CATALOG_DISPLAY_COLLECTION_ITEMS
                doc_ref = self.get_document(path, return_ref = True)
                fields = [{'type': 'field', 'name': name, 'value': value}\
                       for name, value in doc_ref.get().to_dict().items()]
                collections = [{
                    'type': 'collection',
                    'name': i.id,
                    'value': '[' + ', '.join([j.id for j in self.list_documents(f'{path}/{i.id}', shortly = False)[:lm]]) + ']'
                }\
                for i in doc_ref.collections()]
                res = fields + collections
            else:
                res = [{'type': 'document', 'name': i.id} for i in self.list_documents(path, shortly = False)]
        return pd.DataFrame(res)


class DocParser:
    
    @validate_param_in_allowed_list(args_allowed = {3: ['book_pdf']},
                                    kwargs_allowed = {'type': ['book_pdf']})
    def __init__(self, path, name, type = 'book_pdf'):
        self.type = type
        self.name = name
        self.path = path
        self.fs_client = FirestoreClient(os.getenv('DATABASE'))
        self.hash = self._get_hash() 
    
    def _get_hash(self):
        if self.type == 'book_pdf':
            return get_file_sha256(self.path)
        else:
            return ''

    def _get_text(self):
        if self.type == 'book_pdf':
            from pdfminer.high_level import extract_text
            text = extract_text(get_file_path(self.path))
        else:
            text = ''
        return text

    def _filter_dict(self, df, filter_list_name):
        df_remove = self.get_list(name = filter_list_name, return_df = True)
        df = pd.merge(df, df_remove, on = 'word', how = 'left')
        df = df[pd.isnull(df[filter_list_name])][['word', 'freq']].copy()
        df = df.sort_values(['freq'], ascending = False)
        return df

    def get_global_dict(self, update = False):
        if not hasattr(self, 'global_dict') or update:
            try:
                data = self.fs_client.get_document('helpers/global_dict').get('words')
            except NotFound:
                data = []
            self.global_dict = pd.DataFrame(data, columns = ['word', 'translation'])
        return self.global_dict

    def clear_global_dict(self):
        self.fs_client.delete_document('helpers/global_dict')
        self.global_dict = pd.DataFrame()
        print('global dict is cleared')
    
    def update_global_dict(self, append_dict, if_exist_replace = False):

        def update_translation(x):
            if pd.isnull(x['translation_existed']):
                return x['translation_append']
            if if_exist_replace and not pd.isnull(x['translation_append']):
                return x['translation_append']
            return x['translation_existed']
            
        existed_dict = self.get_global_dict(update = True)
        if len(existed_dict) > 0:
            df = existed_dict.merge(append_dict, on = 'word', how = 'outer',
                                    suffixes = ('_existed', '_append'))
            df['translation'] = df.apply(update_translation, axis = 1)
            df = df[['word', 'translation']].copy()
        else:
            df = append_dict
        self.fs_client.create_document(f'helpers/global_dict', 
                                       {'words': df.to_dict(orient = 'records')},
                                       if_exist_replace = True)
        self.global_dict = df
        print(f'helpers/global_dict is updated!')

    def get_list(self, name, return_df = False):
        try:
            doc = self.fs_client.get_document(f'helpers/{name}_list')
        except NotFound:
            self.fs_client.create_document(f'helpers/{name}_list', {'words': []})
            doc = self.fs_client.get_document(f'helpers/{name}_list')
        words = doc.get('words')
        if return_df:
            df = pd.DataFrame({'word': words})
            df[name] = True
            return df
        return words

    def update_list(self, name, append_list):
        existed_list = self.get_list(name)        
        updated_list = set(existed_list + append_list)
        self.fs_client.update_document(f'helpers/{name}_list', {'words': updated_list})
        print(f'helpser/{name}_list is updated!')
    
    def get_dict(self, update = False):
        '''return initial version of freq dict without filtering'''
        if not hasattr(self, 'dict') or update:
            existed_docs = self.fs_client.list_documents('docs', shortly = False)
            try:
                doc = [i for i in existed_docs if i.get().get('hash') == self.hash][0].get()
                name = doc.get('name')
                loaded = doc.get('loaded')
                print(f'found existed doc with the same hash, name: "{name}", loaded: "{loaded}"')
                data = doc.get('dict_initial')
                initial_dict = pd.DataFrame(data)
                initial_dict = initial_dict[['word', 'translation', 'freq']].copy()
            except IndexError:
                initial_dict = self.create_dict()
            self.dict = initial_dict
        return self.dict
            
    def save_csv(self):
        pass
        
    def parse(self, max_size = 500, filter_lists = ['stop', 'known'], if_exist_update = False):

        if not if_exist_update and hasattr(self, 'df_parsed'):
            return self.df_parsed

        lemmatizer = nltk.stem.WordNetLemmatizer()
        text = self._get_text()
        data = nltk.word_tokenize(text)
        
        def get_pos(word):
            pos_tag = nltk.pos_tag([word])[0][1]
            if pos_tag.startswith('J'):
                return 'a'
            elif pos_tag.startswith('V'):
                return 'v'
            elif pos_tag.startswith('R'):
                return 'r'
            else:
                return 'n'
        
        df = pd.DataFrame(data, columns = ['word',])
        df['freq'] = 1
        df = df.groupby(['word']).agg({'freq': 'sum'}).reset_index()        
        df['word'] = df['word'].apply(lambda x: re.sub(r'[^a-zA-Z\-]+', '', x.lower()))
        df = df.groupby(['word'])[['freq']].sum().reset_index()
        df['pos'] = df['word'].apply(get_pos)
        
        df['word'] = df.apply(lambda x: lemmatizer.lemmatize(x['word'], x['pos']), axis = 1)
        df = df[df['word'].apply(lambda x: len(x) >= 3)].copy()
        df = df.groupby(['word'])['freq'].sum().reset_index()        
        df = df[df['word'].apply(lambda x: len(wordnet.synsets(x)) > 0)].copy()

        for i in filter_lists:
            df = self._filter_dict(df, i)
        df = df.iloc[:max_size].copy()
        
        self.df_parsed = df
        return df    

    def translate(self, df):
        
        global_dict = self.get_global_dict()
        _dict = self.df_parsed.merge(global_dict, on = 'word', how = 'left')        
        dict_existed = _dict[~pd.isnull(_dict['translation'])].copy()
        print(f'found {len(dict_existed)} existed words')
        
        words_new = list(_dict[pd.isnull(_dict['translation'])]['word'].values)
        print(f'found {len(words_new)} new words')
        dict_new = translate_phrases(words_new, 'sdk', return_df = True)
        self.update_global_dict(dict_new)
        
        dict_updated = _dict.merge(dict_new, on = 'word', how = 'left', suffixes = ('_existed', '_new'))
        dict_updated['translation'] = dict_updated.apply(lambda x: x['translation_existed'] \
                                     if not pd.isnull(x['translation_existed']) \
                                     else x['translation_new'], axis = 1)
        dict_updated = dict_updated[['word', 'translation', 'freq']].copy()
        self.dict = dict_updated
        return dict_updated
    
    def create_dict(self, filter_lists = ['stop', 'known'], if_exist_replace = False):

        doc_ref = p.fs_client.get_document(f'docs/{self.name}', return_ref = True)
        if doc_ref.get().exists and not if_exist_replace:
            raise Conflict(f'doc with name "{self.name}" already exists, to recreate choose "if_exist_replace = True"')
        
        df = self.parse(if_exist_update = True, filter_lists = filter_lists)
        df = self.translate(df)
        self.fs_client.create_document(f'docs/{self.name}', 
                                       data = {
                                           'name': self.name,
                                           'hash': self.hash,
                                           'loaded': dt.utcnow().isoformat(),
                                           'dict_initial': self.dict.to_dict(orient = 'records')
                                       },
                                      if_exist_replace = True)        
        