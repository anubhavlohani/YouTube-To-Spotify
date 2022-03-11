from urllib import request, response
from googleapiclient.discovery import build
import os

def get_videos(playlist_id):
    api_key = str(os.environ.get("GOOGLE_API_KEY"))
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_titles = []
    nextPageToken = None
    while True:
        pl_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )

        pl_response = pl_request.execute()

        vid_ids = []
        for item in pl_response["items"]:
            vid_ids.append(item['contentDetails']['videoId'])

        vid_request = youtube.videos().list(
            part='contentDetails, snippet',
            id = ','.join(vid_ids)
        )

        vid_response = vid_request.execute()

        for item in vid_response['items']:
            curr_title = item['snippet']['title']
            video_titles.append(curr_title)
        
        nextPageToken = pl_response.get('nextPageToken')
        if not nextPageToken:
            break

    return video_titles