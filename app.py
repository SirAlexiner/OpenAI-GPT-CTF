import markdown
import json
import tempfile
import os
import base64
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
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

# Function to highlight code (Just for fun and authenticity)
def highlight_code_blocks(markdown_text):
    html_result = ""
    # Split the Markdown text into separate code blocks
    try:
        code_blocks = markdown_text.split('```')
    except:
        code_blocks = markdown_text

    # Initialize a flag to alternate between code and non-code blocks
    is_code_block = False

    for i in range(len(code_blocks)):
        if code_blocks[i]:
            if is_code_block:
                # Extract the language identifier (if available)
                code_block = code_blocks[i]
                code_block = code_block.replace('\n\n', '\n')
                if len(code_block) > 1:
                    lang = code_block[:8].strip().split('\n')[0]
                    code_block = code_block.replace(lang, "$ " + lang, 1)
                    if lang == '':
                        lang = "text"
                    # Create a lexer based on the language identifier
                    try:
                        lexer = get_lexer_by_name(lang)
                    except:
                        lexer = get_lexer_by_name('text')
                    # Format Code as HTML with CSS Styling
                    formatter = HtmlFormatter(style='monokai')
                    highlighted_code = highlight(code_block, lexer, formatter)

                    # Include the highlighted code within a code block
                    html_result += highlighted_code
                else:
                    lang = "text"  # Default to "text" if no language identifier is provided
                    # Create a lexer based on the language identifier
                    lexer = get_lexer_by_name(lang, stripall=True)
                    formatter = HtmlFormatter(style='monokai')
                    highlighted_code = highlight(code_block, lexer, formatter)

                    # Include the highlighted code within a code block
                    html_result += highlighted_code
            else:
                # Treat non-code blocks as regular text¨
                code_block = code_blocks[i]
                code_block = code_block.replace('\n\n', '\n')
                html_result += markdown.markdown(code_block)
                # Toggle the code block flag for each iteration
            is_code_block = not is_code_block

    # Return the HTML text
    return html_result

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
                content += text
                yield highlight_code_blocks(content)
        
        response = {
            "role": "assistant",
            "content": content
        }
        data.save(response)

    return Response(event_stream(), mimetype='text/event-stream')

# Run Flask app
if __name__ == '__main__':
    app.run(debug=False)