from fastapi import FastAPI, Request, Response, Cookie, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bson.json_util import dumps
import os, sys, secrets, asyncio
from pprint import pprint
from shutil import make_archive
from pymongo import MongoClient

project_root = os.getcwd()
sys.path.append(f"{project_root}/packages")
spotify_data_path = f'{project_root}/data/Spotify_/'
youtube_data_path = f'{project_root}/data/Youtube/'
AUDIO_DOWNLOAD_DIR = f'{youtube_data_path}/audio'

# Local imports
from packages.Spotify_.SpotifyAPI import SpotifyAPIHelper, SpotifyAPIUtility
from packages.json_helper.json_helper import read_file
from packages.YoutubeApi import YoutubeAPIHelper

# Access scopes for modifying user's data or reading it 
access_scopes = read_file(f'{spotify_data_path}/modify_scopes.json')
read_scope = ' '.join(access_scopes['READ_PLAYLIST'])

user = {
    'login_token':secrets.token_urlsafe(16),
    'user_id':'',
    'user_name':''
    }

progress_status = {}

# Setting up MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client.spotify_me
progress_collection = db.progress

# Setting up the app
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/index", response_class = HTMLResponse)
async def get_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/spotify", response_class = HTMLResponse)
async def get_spotify(request: Request):
    return templates.TemplateResponse("spotify.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def get_home(request: Request, login_token: str = ''):
    print(login_token, user['login_token'])
    # Check if the login status code matches the one sent from spotify_callback
   
    is_logged_in = login_token == user['login_token']
    if is_logged_in:
        return templates.TemplateResponse("home.html", {"request": request, "is_logged_in": is_logged_in, "user_id": user["user_id"], "user_name": user["user_name"]})
    else:
        return templates.TemplateResponse("home.html", {"request": request, "is_logged_in": is_logged_in})
        

@app.get("/login_user", response_class=JSONResponse)
async def login_user(request: Request):
    auth_url = SpotifyAPIHelper.get_authorization_url(custom_redirect_uri='http://localhost:8000/spotify_callback', custom_scope=read_scope)
    
    print(auth_url)
    return {
        'redirect_link': auth_url    
    }

    
@app.get("/spotify_callback", response_class=RedirectResponse)
async def spotify_callback(request: Request, response: Response):
    code = request.query_params.get('code')
    print(code)
    
    response = SpotifyAPIHelper.authorize_new_user(auth_code=code)
    if response.get('status') == 'success':
        user['user_id'] = response['user']['user_id']
        user['user_name'] = response['user']['user_name']

    login_token = secrets.token_urlsafe(16)
    user["login_token"] = login_token

    # Set the login_token as a cookie in the response
    response = RedirectResponse(url=f"/home?login_token={login_token}")
    # response.set_cookie(key="login_token", value=login_token)

    return response


@app.get("/get_user_playlists", response_class= JSONResponse)
async def get_user_playlists(request: Request, user_id: str = ''):
    try: 
        if user_id == '':
            print("User Id not found in the request")
            
            return {
                'status': 'error',
                'message': 'User Id not found in the request'
            }
        
        else:
            playlists = SpotifyAPIUtility.get_user_playlists(user_id=user_id)
            
            return {
                'status': 'success',
                'playlists': playlists,
            }
            
            
    except Exception as e:
        print(f"An error occurred: {type(e).__name__}: {e}")
        # Print additional details if available
        if hasattr(e, 'args'):
            print(f"Error details: {e.args}")
            
        return {
            'status': 'error',
            'comments': 'server-side error',
            'message': e
        }


@app.get("/n-download_playlist")
async def download_playlist(request: Request, playlist_id: str = ''):
    try: 
        if playlist_id == '':
            print("Playlist Id not found in the request")
            
            return {
                'status': 'error',
                'message': 'Playlist Id not found in the request'
            }
        
        else:
            tracks = SpotifyAPIUtility.get_playlist_tracks(playlist_id=playlist_id)
            # pprint(tracks)
            tracks_url = YoutubeAPIHelper.get_tracks_url_by_batch(tracks)
            print(tracks_url)
            
            download_dir = YoutubeAPIHelper.download_tracks_by_batch(tracks_url)
            
            return {
                'status': 'success',
                'message': 'Playlist is downloaded',
                'download_dir': download_dir
            }       
                 
    except Exception as e:
        print(f"An error occurred: {type(e).__name__}: {e}")
        # Print additional details if available
        if hasattr(e, 'args'):
            print(f"Error details: {e.args}")
            
        return {
            'status': 'error',
            'comments': 'server-side error',
            'message': e
        }
        

@app.get("/download_playlist", response_class=JSONResponse)
async def download_playlist(request: Request, background_tasks: BackgroundTasks, playlist_id: str = ''):
    try: 
        if not playlist_id:
            return {'status': 'error', 'message': 'Playlist Id not found in the request'}
        
        process_token = secrets.token_urlsafe(16)
        
        # 1. Getting Tracks
        background_tasks.add_task(get_tracks, playlist_id, background_tasks)
        
        progress_status = {
            'status': 'processing',
            'processToken': process_token,
            'message': 'Getting tracks from Spotify',
        }
        progress_collection.delete_many({})
        progress_collection.insert_one(progress_status)
        
        return {'status': 'processing', 'processToken': process_token, 'message': 'Processing tracks'}
    
    except Exception as e:
        error_message = f"Server-side error occurred: {type(e).__name__}: {e}"
        progress_status = {
            'status': 'error',
            'processToken': process_token,
            'message': error_message
        }
        progress_collection.update_one({}, {'$set': progress_status})
        return {'status': 'error', 'processToken': process_token, 'message': error_message}


@app.get("/check_progress")
async def check_progress():
    try:
        progress_documents = progress_collection.find_one({},{"_id": 0})
        return progress_documents
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)  # Internal Server Error

@app.get("/get_downloads")
async def get_downloads(download_dir: str):
    try:
        # Check if the download directory exists
        if not os.path.exists(download_dir):
            return JSONResponse(content={"error": "Download directory does not exist"}, status_code=404)

        # Zip the folder
        zip_filename = f"{download_dir}/downloaded_files"
        make_archive(zip_filename, 'zip', download_dir)

        # Return the zipped file as a FileResponse
        return FileResponse(path=f'{zip_filename}.zip', media_type="application/zip", filename="downloaded_files.zip")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)  # Internal Server Error




# Other functions

def get_tracks(playlist_id: str, background_tasks: BackgroundTasks):
    try:
        # Fetch tracks from the playlist
        tracks = SpotifyAPIUtility.get_playlist_tracks(playlist_id=playlist_id)
        process_token = secrets.token_urlsafe(16)

        # 2. Searching on YouTube
        background_tasks.add_task(search_on_youtube, tracks, background_tasks)
          
        # Update progress status
        progress_status = {
            'status': 'processing',
            'processToken': process_token,
            'message': 'Searching tracks on YouTube',
        }
        progress_collection.update_one({}, {'$set': progress_status})
    except Exception as e:
        error_message = f"Failed to get tracks: {type(e).__name__}: {e}"
        progress_status = {
            'status': 'error',
            'processToken': process_token,
            'message': error_message
        }
        progress_collection.update_one({}, {'$set': progress_status})


def search_on_youtube(tracks, background_tasks: BackgroundTasks):
    try:
        # Search for each track on YouTube
        tracks_url = YoutubeAPIHelper.get_tracks_url_by_batch(tracks)
        process_token = secrets.token_urlsafe(16)
        
        # Update progress status
        progress_status = {
            'status': 'processing',
            'processToken': process_token,
            'message': 'Downloading tracks',
        }
        progress_collection.update_one({}, {'$set': progress_status})

        
        # 3. Downloading Tracks
        background_tasks.add_task(download_tracks, tracks_url, background_tasks)
    
    except Exception as e:
        error_message = f"Failed to search on YouTube: {type(e).__name__}: {e}"
        progress_status = {
            'status': 'error',
            'processToken': process_token,
            'message': error_message
        }
        progress_collection.update_one({}, {'$set': progress_status})


def download_tracks(tracks_url, background_tasks: BackgroundTasks):
    # try:
        # Download tracks
    download_dir = YoutubeAPIHelper.download_tracks_by_batch(tracks_url)
    process_token = secrets.token_urlsafe(16)

    # Update progress status
    progress_status = {
        'status': 'complete',
        'processToken': process_token,
        'message': 'Download complete',
        'download_dir': download_dir
    }
    progress_collection.update_one({}, {'$set': progress_status})
    

    # except Exception as e:
    #     error_message = f"Failed to download tracks: {type(e).__name__}: {e}"
    #     progress_status = {
    #         'status': 'error',
    #         'processToken': process_token,
    #         'message': error_message
    #     }
    #     progress_collection.update_one({}, {'$set': progress_status})



