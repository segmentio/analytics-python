import requests
import os
from urllib.parse import urlencode
import webbrowser

CLIENT_ID = "Iv1.9332e33a45a46e2f"
CLIENT_SECRET = "ddfc4878523bf3e7038f2e72ca0f3900382a95e9"
REDIRECT_URI = "https://httpbin.org/anything"
BASE_API_ENDPOINT = "https://oauth2.segment.build"

"""
Github App
CLIENT_ID = "Iv1.9332e33a45a46e2f"
CLIENT_SECRET = "ddfc4878523bf3e7038f2e72ca0f3900382a95e9"
REDIRECT_URI = "https://httpbin.org/anything"
BASE_API_ENDPOINT = "https://api.github.com/user"
endpoint = "https://github.com/login/oauth/authorize"

AFTER CODE ENDPOINT
endpoint = "https://github.com/login/oauth/access_token"

"""

"""
Here's the key file for OAuth2.  
You'll need to specify a different endpoint server, api.segment.build
The write key for the source is TEBWeMLQWxtJjW8B91Hu5bujQLqhpLUR
The Client/App ID: 2TlKP068Khdw4jZaCHuWjXmvui2
The Key ID: 2TlKOw1a7n9tUUmVK1ISKnnJ0hA
"""

params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": "user"
}

endpoint = "https://oauth2.segment.build/login/oauth/authorize"
endpoint = endpoint + '?' + urlencode(params)
webbrowser.open(endpoint)

code = input("Enter the Code: ")

print("Got Code")

params = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": code,
}
endpoint = "https://oauth2.segment.build/token"
response = requests.post(endpoint, params=params, headers = {"Accept": "application/json"}).json()
access_token = response['access_token']
print("Got Access Token")

session = requests.session()
session.headers = {"Authorization": f"token {access_token}"}

base_api_endpoint = BASE_API_ENDPOINT

response = session.get(base_api_endpoint)
print(response)

