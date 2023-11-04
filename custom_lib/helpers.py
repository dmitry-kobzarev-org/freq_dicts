import hashlib
from google.cloud import translate_v3 as translate
import os
import pandas as pd
from dk_google.cloud.iam import get_credentials

def get_file_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b''):
            sha256.update(block)
    return sha256.hexdigest()

def translate_phrases(phrases_list, cred_type = False, chunksize = 50, return_df = False):
    
    if not cred_type:
        cred_type = os.getenv('CRED_TYPE') or 'service'
        
    client = translate.TranslationServiceClient(
        credentials = get_credentials(cred_type = cred_type)
    )
    parent = client.common_location_path(
        project = os.getenv('project_id'), 
        location = os.getenv('region')
    )

    res_list = []
    phrases_rest = copy.deepcopy(phrases_list)
    while len(phrases_rest) > 0:
        phrases_part = copy.deepcopy(phrases_rest[:chunksize])
        phrases_rest = copy.deepcopy(phrases_rest[chunksize:])
        r = client.translate_text(
            request = {
                'contents': phrases_part,
                'parent': parent,
                'source_language_code': 'en',
                'target_language_code': 'ru'
            }
        )
        res_list = res_list + [(i, j.translated_text) for i, j in zip(phrases_part, r.translations)]
        print(f'append {len(phrases_part)} words, the rest is {len(phrases_rest)}')
    
    if return_df:
        return pd.DataFrame(res_list, columns = ['word', 'translation'])

    return res_list
