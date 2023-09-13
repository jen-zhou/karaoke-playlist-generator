from flask import Request
import gspread
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv

# Initialize Google Sheets API
spreadsheet_name = 'karaoke (Responses)'
scope = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.readonly']

creds = None
# The file token.json stores the user's access and refresh tokens, 
# and is created automatically when the authorization flow completes for the first time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', scope)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', scope)
        creds = flow.run_local_server(port=8080)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

client = gspread.authorize(creds)
sheet = client.open(spreadsheet_name).sheet1  # replace with sheet name

# Initialize YouTube API
youtube_service = build("youtube", "v3", credentials=creds)

def search_lyric_video(song_name, artist):
    # Use the YouTube API to search for lyric videos
    query = f"{song_name} {artist} lyrics"
    search_response = youtube_service.search().list(
        q=query,
        type="video",
        part="id",
        maxResults=1
    ).execute()

    if search_response.get("items"):
        video_id = search_response["items"][0]["id"]["videoId"]
        return video_id

def create_playlist(title):
    # Create a new YouTube playlist
    playlist_response = youtube_service.playlists().insert(
        part="snippet",
        body={
            "snippet": {
                "title": title,
                "description": "Karaoke Playlist"
            }
        }
    ).execute()

    return playlist_response["id"]

def get_playlist_id_by_title(playlist_title):
    # Get your channel ID by making a request to the 'channels' endpoint
    channels_response = youtube_service.channels().list(
        mine=True,  # Get the channel associated with your API key
        part='id'
    ).execute()

    # Check if any results were found
    if 'items' in channels_response:
        channel_id = channels_response['items'][0]['id']

        # Make a search request to find the playlist by name and your channel ID
        search_response = youtube_service.search().list(
            q=playlist_title,
            channelId=channel_id,
            type='playlist',
            part='id',
            maxResults=1  # You expect only one result for a unique name
        ).execute()
        print('yo', search_response)

        if 'items' in search_response:
            if len(search_response['items']) == 0:
                return None
            print('hi', search_response)
            return search_response['items'][0]['id']['playlistId']
        else: 
            return None
    return None


def add_video_to_playlist(playlist_id, id):

    youtube_service.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": id
                }
            }
        }
    ).execute()




id = create_playlist(spreadsheet_name)

for row in sheet.get_all_records():
    song_name = row["song name"]
    artist = row["artist"]
    title = f"{song_name} - {artist}"
    print(song_name)

    vid_id = search_lyric_video(song_name, artist)
    if id:
        add_video_to_playlist(id, vid_id)
