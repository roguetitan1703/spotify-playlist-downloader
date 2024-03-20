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


@app.get("/download_playlist")
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
        

