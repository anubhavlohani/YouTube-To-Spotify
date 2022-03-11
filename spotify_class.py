from email import header
from pydoc import cli
import requests
import datetime
import json
import base64
from urllib.parse import urlencode


'''
This class is supposed to be used after an initial access_token has been generated
Will use this class to generate a playlist in the user's account
&
Add tracks to that playlist
'''

class SpotifyAPI():
    access_token = None
    refresh_token = None
    access_token_expires = datetime.datetime.now()
    token_url = "https://accounts.spotify.com/api/token"
    client_id = ""
    client_secret = ""

    def __init__(self, client_id, client_secret, data=None, access_token=None, refresh_token=None):
        '''
        data is the json data returned by the request that contains access_token,
        expires_in & refresh_token
        '''
        self.client_id = client_id
        self.client_secret = client_secret
        if data != None:
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            expires_in = data["expires_in"] # seconds
            self.access_token_expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        else:
            self.access_token = access_token
            self.refresh_token = refresh_token
            self.access_token_expires = self.access_token_expires + datetime.timedelta(seconds=3600)

        
    def get_client_credentials(self):
        """
        Return a base64 ecoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_id == None or client_secret == None:
            raise Exception("Must set client_id and client_secret")
        client_creds = f"{self.client_id}:{self.client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def validate_access_token(self):
        if self.access_token_expires < datetime.datetime.now():
            return False
        return True

    def refresh_access_token(self):
        code_payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        headers = {
            "Authorization": "Basic {}".format(self.get_client_credentials()),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        req = requests.post(self.token_url, data=code_payload, headers=headers)
        data = req.json()
        self.access_token = data["access_token"]
        expires_in = data["expires_in"] # seconds
        self.access_token_expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        return

    def get_access_token(self):
        if not self.validate_access_token():
            self.refresh_access_token()
        return self.access_token

    def create_playlist(self, username, playlist_name, playlist_description, public=False, collaborative=False):
        code_payload = json.dumps({
            "name": playlist_name,
            "description": playlist_description,
            "public": public,
            "collaborative": collaborative
        })
        headers = {
            "Authorization": "Bearer {}".format(self.get_access_token()),
            "Content-Type": "application/json"
        }
        url = "https://api.spotify.com/v1/users/{}/playlists".format(username)
        res = requests.post(url, data=code_payload, headers=headers)
        return res

    def search_track(self, query=None):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query, dict):
            query = " ".join([f"{key}:{val}" for key, val in query.items()])
            print(query)
        query_params = urlencode({"q": query, "type": "track"})
        
        headers = {
            "Authorization": "Bearer {}".format(self.get_access_token()),
            "Content-Type": "application/json"
        }
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = "{}?{}".format(endpoint, query_params)
        res = requests.get(lookup_url, headers=headers)
        if res.status_code not in range(200, 299):
            return ""
        res_data = res.json()
        if len(res_data["tracks"]["items"]):
            return res_data["tracks"]["items"][0]["id"]
        return ""