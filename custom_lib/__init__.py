import os
import pandas as pd
from dk_google.cloud.iam import get_credentials
from dk_google.helpers import if_exist_replace
from google.cloud import firestore
from google.cloud.exceptions import NotFound

class FirestoreClient:
    
    def __init__(self, database):
        self.project_id = os.getenv('PROJECT_ID')
        self.cred_type = os.getenv('CRED_TYPE')
        self.creds = get_credentials(self.cred_type)
        self.client = firestore.Client(project = self.project_id, database = database)
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
        ls = list(self.client.collection(collection).list_documents())
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
