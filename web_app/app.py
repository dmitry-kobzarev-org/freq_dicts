from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import time
import hashlib
import random
import string
import json
from dk_google.local import create_local_file
from dk_google import *

init_client = Client()
init_client.init_script()

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

def generate_unique_id(unique_word):
    # Get the current timestamp (in seconds)
    timestamp = str(int(time.time()))

    # Generate a random component (4 characters)
    random_component = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(4))

    # Combine the timestamp, unique word, and random component
    input_string = timestamp + unique_word + random_component

    # Hash the input string using SHA-256
    unique_id = hashlib.sha256(input_string.encode()).hexdigest()

    # Truncate to 12 characters
    unique_id = unique_id[:12]
    return unique_id

info_list = [{
    'counter': i,
    'id': generate_unique_id(f'hello_{i}'),
    'info': f'hello_{i}',
    'press': None
} for i in range(100)]
counter = 0

@app.route('/')
def index():
    return render_template('index.html', data = info_list[counter])

@app.route('/api/get_data/')
def get_data():
    data = info_list[counter]
    return data

@app.route('/api/process_log/', methods = ['POST'])
def send_log():
    global counter
    data = request.json
    print(data)
    info_list[
        [i.get('counter') for i in info_list if i.get('id') == data.get('info_id')][0]
    ]['press'] = data.get('button')
    create_local_file('tmp/info_list.json', json.dumps(info_list))
    counter += 1

    return jsonify({'message': 'log was processed'})

if __name__ == '__main__':
    app.run(debug = True)
