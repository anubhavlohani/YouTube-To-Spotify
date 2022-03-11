import base64
from flask import Flask, render_template, request, redirect, url_for
import os
import json
import requests
from datetime import datetime
from urllib.parse import urlencode

from spotify_class import SpotifyAPI
from preparing_names import create_queries
from v3.app_local import PLAYLIST_ID
from youtube_side import get_videos
current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

#  Client Keys
CLIENT_ID = str(os.environ.get("CLIENT_ID"))
CLIENT_SECRET = str(os.environ.get("CLIENT_SECRET"))

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


REDIRECT_URI = "https://youtube-playlist-to-spotify.herokuapp.com/callback"
SCOPE = "playlist-modify-public playlist-modify-private"

SONGS_FOUND = []
SONGS_NOT_FOUND = []

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        os.environ["USERNAME"] = str(request.form["username"])
        query_params = urlencode({
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE
        })
        return redirect("{}?{}".format(SPOTIFY_AUTH_URL, query_params))

    return render_template("home.html")

@app.route("/callback", methods=["GET"])
def callback():
    auth_code = request.args["code"]
    code_payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }
    client_creds_b64 = base64.b64encode(("{}:{}".format(CLIENT_ID, CLIENT_SECRET)).encode())
    headers = {
        "Authorization": "Basic {}".format(client_creds_b64.decode()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    res = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)
    
    SPOTIFY = SpotifyAPI(CLIENT_ID, CLIENT_SECRET, res.json())

    os.environ["ACCESS_TOKEN"] = str(SPOTIFY.access_token)
    os.environ["REFRESH_TOKEN"] = str(SPOTIFY.refresh_token)
    os.environ["ACCESS_TOKEN_EXPIRES"] = SPOTIFY.access_token_expires.strftime("%Y-%m-%d %H:%M:%S")

    return redirect(url_for("create_playlist"))

@app.route("/create-playlist", methods=["GET", "POST"])
def create_playlist():
    if request.method == "POST":
        playlist_name = request.form["playlist_name"]
        playlist_description = request.form["playlist_description"]

        access_token = os.environ.get("ACCESS_TOKEN")
        refresh_token = os.environ.get("REFRESH_TOKEN")
        access_token_expires = datetime.strptime(os.environ.get("ACCESS_TOKEN_EXPIRES"), "%Y-%m-%d %H:%M:%S")
        SPOTIFY = SpotifyAPI(CLIENT_ID, CLIENT_SECRET, access_token=access_token, refresh_token=refresh_token, access_token_expires=access_token_expires)
        
        USERNAME = os.environ.get("USERNAME")
        r = SPOTIFY.create_playlist(USERNAME, playlist_name, playlist_description)

        if r.status_code in range(200, 299):
            os.environ["SPOTIFY_PLAYLIST_ID"] = r.json()["id"]
            return redirect(url_for("youtube_playlist"))

    return render_template("create_playlist.html")

@app.route("/youtube-playlist", methods=["GET", "POST"])
def youtube_playlist():
    if request.method == "POST":
        link = request.form["playlist_link"]
        link = link.split("=")[-1]
        os.environ["YT_PLAYLIST_LINK"] = str(link)

        return redirect(url_for("adding_songs", curr_index=0))

    return render_template("youtube_playlist.html")

@app.route("/adding-songs/<curr_index>", methods=["GET", "POST"])
def adding_songs(curr_index):
    curr_index = int(request.path.split('/')[-1])

    access_token = os.environ.get("ACCESS_TOKEN")
    refresh_token = os.environ.get("REFRESH_TOKEN")
    access_token_expires = datetime.strptime(os.environ.get("ACCESS_TOKEN_EXPIRES"), "%Y-%m-%d %H:%M:%S")
    SPOTIFY = SpotifyAPI(CLIENT_ID, CLIENT_SECRET, access_token=access_token, refresh_token=refresh_token, access_token_expires=access_token_expires)

    YOUTUBE_VIDEOS = get_videos(os.environ.get("YT_PLAYLIST_LINK"))

    search_queries = create_queries(YOUTUBE_VIDEOS[curr_index])
    track_id = None
    for query in search_queries:
        temp = SPOTIFY.search_track(query)
        if temp != None:
            track_id = temp
    
    if track_id is None:
        SONGS_NOT_FOUND.append(YOUTUBE_VIDEOS[curr_index])
    else:
        SONGS_FOUND.append(YOUTUBE_VIDEOS[curr_index])
        headers = {
            "Authorization": "Bearer {}".format(SPOTIFY.get_access_token()),
            "Content-Type": "application/json"
        }
        code_payload = json.dumps({
            "uris": ["spotify:track:" + track_id]
        })

        PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID")
        r = requests.post("https://api.spotify.com/v1/playlists/{}/tracks".format(PLAYLIST_ID), data=code_payload, headers=headers)

    if curr_index == len(YOUTUBE_VIDEOS)-1:
        # all songs searched
        return render_template("done.html", songs_found = SONGS_FOUND, songs_not_found = SONGS_NOT_FOUND)
    
    else:
        return render_template("added_songs.html", songs_found = SONGS_FOUND, songs_not_found = SONGS_NOT_FOUND, curr_index="0, URL=http://192.168.1.4:8080/adding-songs/{}".format(curr_index+1))

if __name__ == "__main__":
    app.run()