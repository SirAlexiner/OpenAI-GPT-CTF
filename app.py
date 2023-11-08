import json
import tempfile
import os
import base64
from flask import Flask, stream_template, request, jsonify, session, Response
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

# Import OpenAI GPT file
# We specify the AI model here
import ai.gpt as gpt
model = "gpt-4"

# Load JSON Handling file
import handler.json_handler as jsonHand

# Set AES Key and IV to random bytes
secret_key = os.urandom(32)
secret_iv= os.urandom(16)

# Initialize Flask
app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.urandom(32)

# Function to create a temporary JSON file for the session
def create_session_json():
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    session['temp_json'] = temp_file.name
    temp_file.close()
    with open(session['temp_json'], 'w') as json_file:
        json.dump([], json_file)

# Specify Index route of the flask application
@app.route('/')
def index():
    # Get the Key and IV as global
    global secret_key
    global secret_iv
    # set the key and IV again to avoid error.
    secret_key = os.urandom(32)
    secret_iv = os.urandom(16)
    # Set key and IV as session cookies
    session['encryption_key'] = base64.b64encode(secret_key).decode('utf-8')
    session['iv'] = base64.b64encode(secret_iv).decode('utf-8')
    # Create a session json to contain the chat log
    create_session_json()
    # Load HTML
    return stream_template('index.html', model=model.upper())

# Function to AES Decrypt the JSON data
def decrypt_message(encrypted_message):
    # Get Key and IV from session cookie
    key = base64.b64decode(session.get('encryption_key', ''))
    iv = base64.b64decode(session.get('iv', ''))
    # Construct a AES cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Decode from Base64 decrypt rhe AES and unpad the bytes
    decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(encrypted_message)), AES.block_size)
    # Decode the bytes to utf-8
    decrypted_message = decrypted_bytes.decode('utf-8')
    # Parse the decrypted JSON string into a JSON Object
    json_data = json.loads(decrypted_message)
    # Return the Json Object
    return json_data

# Function to Encrypt the AES encrypted JSON data
def encrypt_message(message):
    # Get Key and IV from session cookie
    key = base64.b64decode(session.get('encryption_key', ''))
    iv = base64.b64decode(session.get('iv', ''))
    # Construct a AES cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Encode to Base64 pad the bytes and encrypt
    encrypted_data = cipher.encrypt(pad(message.encode(), AES.block_size))
    # Return encrypted data
    return encrypted_data

# Get route to get the user input
@app.route('/get', methods=['GET'])
def process_data():
    # Get the user input
    user_input = request.args.get('input')

    # Format the user input as OpenAI user call
    data = {'role': 'user', 'content': user_input}
    # Serialize obj to a JSON formatted str.
    json_body = json.dumps(data)
    # AES encrypt the message
    encrypted_json = encrypt_message(json_body)

    # Return the AES encrypted str as JSON
    result = {'encrypted_data': base64.b64encode(encrypted_json).decode('utf-8')}
    return jsonify(result)

# Send POST route to send the response to OpenAI
@app.route('/send', methods=['POST'])
def send():
    JSON = session['temp_json']
    # Get the AES encrypted data
    user_message = request.json.get('encrypted_data')

    # Decrypt the user input
    decrypted_message = decrypt_message(user_message)

    # Process user input and generate GPT response, providing the temp JSON for chat logging
    gpt_response = gpt.get_gpt_response(JSON, decrypted_message, model)

    # Function to send GPT respons as a text stream 
    def event_stream():
        data = jsonHand.Data(JSON)

        content = ""

        for line in gpt_response:
            text = line.choices[0].delta.get('content', '')
            
            if len(text):
                yield text

            content += text

            response = {
                "role": "assistant",
                "content": content
            }

        data.save(response)

    return Response(event_stream(), mimetype='text/event-stream')

# Run Flask app
if __name__ == '__main__':
    app.run(debug=False)