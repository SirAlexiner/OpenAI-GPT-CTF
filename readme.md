## Writeup: Web/Crypto/OSINT – “Gaslighting”

### Task Description

We informed GPT about the flag but instructed it to keep it a secret, avoiding any disclosure. However, someone claims they acquired the flag from GPT. Can you uncover how?

### Step-by-Step Participant Guide for Extracting the Flag from GPT:

1. **Engaging with GPT:**
   - Upon accessing the page, participants will quickly notice that the HTML source code, CSS, and images provide no critical details besides mock text.
   - Engaging with GPT, participants should deduce that coaxing GPT directly through the chat functionality would be challenging due to strict guidelines prohibiting flag disclosure.

2. **Discovering Server Information:**
   - Participants should start by meticulously analyzing the script.js file to uncover any references or comments hinting at the server's structure, crucial for proceeding with the challenge.

3. **Decryption Process (RSA):**
   - Encountering 'secret.js,' participants should take note of the message, and it's capitalized words, hinting at exploring the console.
   - Following this cue, participants should access the console and execute the 'get_private_key' command, unveiling content sent over POST and allowing them to retrieve the Private RSA key after inspecting the network tab.

4. **Understanding Flask Server Session Vulnerability:**
   - Participants should conduct external searches to discover a vulnerability in the Flask server, involving reversible session encryption despite a randomized byte key.
   - Using a web resource, participants should decrypt the session cookie found on the site within the application tab.

5. **Decryption Process (AES):**
   - With the RSA private key, participants should proceed to decrypt the session data. Correctly performed, this should reveal a JSON structure containing the necessary Encryption Key and IV for further decryption.
   - Using additional external searches, participants should conclude that the challenge employs AES encryption for stronger encryptions based on the information in the session data (Key and IV).

6. **Transitioning to Advanced Tools:**
   - Observing the POST/GET requests, participants should shift to using BurpSuite or Postman to manipulate and analyze these requests, recognizing the challenge's requirements.

7. **Continuing the Decryption Process (AES):**
   - Using the obtained AES Encryption Key and IV, participants should decrypt the POST data, resulting in an output structured as follows:
   <br>`{'role': 'users', 'content': [User Message]}`.

8. **Maintaining Session Continuity:**
   - To ensure decryption continuity, participants should avoid page refreshes, understanding that this action generates a new session and new encryption values.

9. **Exploration and Experimentation:**
   - For a deeper understanding, participants should experiment by encrypting a personalized message using the same AES values. Additionally, exploring OpenAI’s API roles provides insights into GPT's behavior influenced by the "system" role.

10. **Strategic Influence on GPT:**
    - Finally, to retrieve the flag, participants should craft a system prompt contradicting the initial constraints and alter a POST request within Burp or Postman with this data and send it. If the steps are completed correctly, participants should be rewarded with the revelation of the flag within the response.