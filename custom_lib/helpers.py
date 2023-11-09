import hashlib
from google.cloud import translate_v3 as translate
import os
import pandas as pd
from google.cloud import texttospeech
from dk_google.cloud.iam import get_credentials
from datetime import timedelta, datetime as dt
from dk_google.cloud.storage import StorageClient

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

def update_reword_tables():

    db_file = 'tmp/reword_en.backup'
    conn = sqlite3.connect(db_file)
    
    tables = list(pd.read_sql_query('select name from sqlite_master where type = "table"', conn).name)
    for t in tables:
        try:
            df = pd.read_sql_query(f'select * from {t}', conn)
            df.to_gbq(f'reword.raw_{t.lower()}', if_exists = 'replace')
            print(f'add table "{t.lower()}"')
        except:
            print(f'error with "{t.lower()}"')
    conn.close()

def text_to_speech(text, output_file):
    
    client = texttospeech.TextToSpeechClient(credentials = get_credentials('sdk'))

    synthesis_input = texttospeech.SynthesisInput(text = text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file, "wb") as out_file:
        out_file.write(response.audio_content)

def generate_signed_url(bucket_name, blob_name, expiration_sec = 3600):
    client = StorageClient('sdk').client
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    signed_url = blob.generate_signed_url(
        expiration = dt.utcnow() + timedelta(seconds = expiration_sec))

    return signed_url