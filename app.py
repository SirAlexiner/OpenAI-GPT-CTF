import json
import tempfile
import logging
from logging.handlers import RotatingFileHandler
import os
import base64
from flask import Flask, stream_template, request, jsonify, session, Response
from flask.logging import default_handler
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad, pad

# Import OpenAI GPT file
# We specify the AI model here
import ai.gpt as gpt
model = "gpt-4o"

# Load JSON Handling file
import handler.json_handler as jsonHand

# Initialize Flask
app = Flask(__name__)

def configure_logging(app):
    # Logging Configuration
    if app.config['LOG_WITH_GUNICORN']:
        gunicorn_error_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers.extend(gunicorn_error_logger.handlers)
        app.logger.setLevel(logging.DEBUG)
    else:
        file_handler = RotatingFileHandler('instance/flask-user-management.log',
                                           maxBytes=16384,
                                           backupCount=20)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(threadName)s-%(thread)d: %(message)s [in %(filename)s:%(lineno)d]')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Remove the default logger configured by Flask
    app.logger.removeHandler(default_handler)

    app.logger.info('...Starting the Flask Server...')

# Set a secret key for session management
app.secret_key = os.urandom(32)

# Generate RSA keys
key = RSA.generate(2048)
private_key = key.export_key()
public_key = key.publickey().export_key()

# Set AES Key and IV to random bytes
secret_key = get_random_bytes(32)
secret_iv = get_random_bytes(16)

# Use the public key for encryption using PKCS1_OAEP
def rsa_encrypt(keys):
    combined_key = ''.join(keys)
    recipient_key = RSA.import_key(public_key)
    cipher_rsa = PKCS1_OAEP.new(recipient_key, hashAlgo=SHA256)
    encrypted_message = cipher_rsa.encrypt(combined_key.encode())
    return base64.b64encode(encrypted_message).decode('utf-8')

# Create a JSON object containing the AES key and IV
key_iv_json = {
    'encypted_data_1': rsa_encrypt("Base64 Key: " + base64.b64encode(secret_key).decode('utf-8')),
    'encrypted_data_2': rsa_encrypt("Base64 IV: " + base64.b64encode(secret_iv).decode('utf-8'))
}

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
    # Create a session json to contain the chat log
    create_session_json()
    # Store RSA public key and encrypted key/IV in session, base64 encoded
    session['encrypted_data'] = key_iv_json

    # Load HTML
    return stream_template('index.html', model=model.upper())

# Function to AES Decrypt the JSON data
def decrypt_message(encrypted_message):
    # Construct a AES cipher
    cipher = AES.new(secret_key, AES.MODE_CBC, secret_iv)
    # Decode from Base64, decrypt the AES and unpad the bytes
    decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(encrypted_message)), AES.block_size)
    # Decode the bytes to utf-8
    decrypted_message = decrypted_bytes.decode('utf-8')
    # Parse the decrypted JSON string into a JSON Object
    json_data = json.loads(decrypted_message)
    # Return the Json Object
    return json_data

# Function to Encrypt the AES encrypted JSON data
def encrypt_message(message):
    # Construct a AES cipher
    cipher = AES.new(secret_key, AES.MODE_CBC, secret_iv)
    # Encode to Base64, pad the bytes and encrypt
    encrypted_data = cipher.encrypt(pad(message.encode(), AES.block_size))
    # Return encrypted data
    return base64.b64encode(encrypted_data).decode('utf-8')

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
    result = {'encrypted_data': encrypted_json}
    return jsonify(result)

@app.route('/secrets', methods=['POST'])
def secrets():
    return private_key.decode('utf-8')

# POST route to send the response to OpenAI
@app.route('/send', methods=['POST'])
def send():
    JSON = session['temp_json']
    # Get the AES encrypted data
    user_message = request.json.get('encrypted_data')

    # Decrypt the user input
    decrypted_message = decrypt_message(user_message)

    # Define the actual supported roles for GPT-4o by OpenAI
    supported_roles = ['system', 'user']

    if 'role' in decrypted_message and decrypted_message['role'] not in supported_roles:
        # Role is not supported, return an error response
        return f"## External Server Error\nThe server encountered an external error and was unable to complete your request. There is an error in the request.\n\n\n# Cause:\n {decrypted_message['role']} is not an OpenAI supported role."

    # Process user input and generate GPT response, providing the temp JSON for chat logging
    gpt_response = gpt.get_gpt_response(JSON, decrypted_message, model)


    # Function to send GPT response as a text stream
    def event_stream():
        data = jsonHand.Data(JSON)

        content = ""

        for line in gpt_response:
            text = line.choices[0].delta.content
            
            if not text == None:
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
