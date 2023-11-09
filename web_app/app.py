from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import time
import hashlib
import random
import string
import json
from dk_google.local import create_local_file
from dk_google import *
from functools import wraps

init_client = Client()
init_client.init_script()

import sys
sys.path.append(os.getenv('ROOT_FULL_PATH'))

load_dotenv()  # Load environment variables from .env file

from custom_lib import FirestoreClient
from custom_lib.helpers import generate_signed_url

app = Flask(__name__)

def get_data(size, user = 'dima'):
    client = FirestoreClient('freq-dicts')
    cur_list = client.get_document('users/dima').get('current_list')
    data_part = copy.deepcopy(cur_list[:size])
    cur_list_updated = copy.deepcopy(cur_list[size:] + cur_list[:size])
    client.update_document('users/dima', 
                           data = {'current_list': cur_list_updated})
    for i in data_part:
        i['signed_url'] = generate_signed_url('dk-lang-reword', i.get('gcs_rel_path'))
    return data_part

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or session['user'] != authorized_user['username']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

app.secret_key = 'hello_dima'  # Replace with a strong secret key
authorized_user = {
    'username': 'dima',
    'password': 'hello'
}

@app.route('/')
@requires_auth
def app_page():
    return render_template('app.html')

@app.route('/api/get_data/')
@requires_auth
def get_data_api():
    user = session.get('user')
    size = int(request.args.get('size'))
    data = get_data(size)
    return jsonify(data)

@app.route('/api/process_logs/', methods = ['POST'])
def send_log_api():
    pass

    return jsonify({'message': 'log was processed'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == authorized_user['username'] and password == authorized_user['password']:
            session['user'] = username
            return redirect(url_for('app_page'))
        else:
            return 'Invalid credentials. Please try again.'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))
