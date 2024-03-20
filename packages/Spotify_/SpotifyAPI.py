# Importing modules to handle requests, server and encoding
import requests, webbrowser, http.server, socketserver, threading
import base64, json
from urllib.parse import urlencode

# Importing modules for paths and environment file
import os, sys, time
from dotenv import load_dotenv, set_key

# Importing logging module
import logging, colorlog

# Adding the project's root directory to the path
project_root = os.getcwd()
sys.path.append(project_root)
# sys.path.append(f'{project_root}/data')

# Importing local modules
from packages.json_helper.json_helper import read_file

# Initialising the paths for data files
spotify_data_path = f'{project_root}/data/Spotify_/'
log_data_path = f'{project_root}/data/logs/'

# Loading the .env file
env_file = f'{spotify_data_path}/.env'
load_dotenv(env_file)

# Loading environment variables 

# Variables dealing with authorization and tokens
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')  
redirect_uri = os.getenv('REDIRECT_URI')
fast_redirect_uri = os.getenv('FAST_REDIRECT_URI')
get_auth_code_url = os.getenv('GET_AUTHORIZATION_CODE_URL')
auth_code = os.getenv('AUTHORIZATION_CODE')
get_access_token_url = os.getenv('GET_ACCESS_TOKEN_URL')

# Tokens
refresh_token = os.getenv('REFRESH_TOKEN')
access_token = os.getenv('ACCESS_TOKEN')
expires_in = 0

# Access scopes for modifying user's data or reading it 
access_scopes = read_file(f'{spotify_data_path}/modify_scopes.json')
scope = ' '.join(access_scopes['MODIFY_PLAYBACK_LISTENING_PLUS']+access_scopes['MODIFY_LIBRARY_PLAYLIST_PLUS'])

# Urls for getting data from Spotify API
get_recommendations_url = os.getenv('GET_RECOMMENDATIONS_URL')
get_current_user_profile_url = os.getenv('GET_CURRENT_USER_PROFILE_URL')
get_user_playlists_url = os.getenv('GET_USER_PLAYLISTS_URL')
get_playlist_tracks_url = os.getenv('GET_PLAYLIST_TRACKS_URL')

# Urls for modifying data in Spotify API
create_playlist_url = os.getenv('CREATE_PLAYLIST_URL')
edit_items_in_playlist_url = os.getenv('EDIT_ITEMS_IN_PLAYLIST_URL')

# User data
user_id = os.getenv('USER_ID')
user_name = os.getenv('USER_NAME')


# Implenting a logger function for seperate module logging
class Logger:
    def __init__(self, log_name, log_file, log_to_console=False, debug_mode=None):
        # Name of the logger to differentiate later
        self.log_name = log_name
        # The log file where the log statements are to be saved
        self.log_file = log_file
        # Whether to log to console or not (only needed when debugging through console)
        self.log_to_console = log_to_console
        # Whether to log in debug mode or not
        self.debug_mode = debug_mode
        
        # Initialising the logger
        self.logger = colorlog.getLogger(self.log_name)
        # Setting the logger to the lowest level DEBUG-> INFO-> WARNING-> ERROR -> CRITICAL, a logger only logs statements which are on or above it's level
        self.logger.setLevel(logging.DEBUG)
        # Managing all the handlers
        self.handlers = {}        
        # Setting up a custom color formatter for better visuals of the log and easy readability
        self.color_formatter = colorlog.ColoredFormatter(
            '%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # Setting up the loggers handlers
        self.setup_handlers()
        
        
    # Function to setup the file handler which will log to the specified log file 
    def setup_file_handler(self):
        file_handler = logging.FileHandler(self.log_file)
        # Set the level to DEBUG to allow all the logs
        file_handler.setLevel(logging.DEBUG)
        # Add the handler to the handlers dictionary
        self.handlers['file_handler'] = file_handler

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)
        
        # Set the formatter to the color_formatter for the file handler
        file_handler.setFormatter(self.color_formatter)
    
    
    # Function to setup the console handler which will log to the console, and will be usef for immediate feedback during development
    def setup_console_handler(self):
        console_handler = logging.StreamHandler()
        # Set the level to CRITICAL if log_to_console if False making the console_logger to only log statements to console if they are CRITICAL
        console_handler.setLevel(logging.CRITICAL if not self.log_to_console else logging.DEBUG)
        # Add the handler to the handlers dictionary
        self.handlers['console_handler'] = console_handler
        
        # Add the console_handler to the logger
        self.logger.addHandler(console_handler)
        
        # Set the formatter to the color_formatter for the file handler
        console_handler.setFormatter(self.color_formatter)
        

    # Setup all the handlers at once
    def setup_handlers(self):
        self.setup_file_handler()
        self.setup_console_handler() 

        # If a log file is opened to be read, it makes sure the contents are not cleared and vice versa   
        if not self.debug_mode:
            self.clear_log_file()
            # self.log_message('info', 'Starting Program')
        
        
    # Enable console logging if it was disabled previously
    def enable_console_logging(self):
        self.log_to_console = True
        if self.handlers['console_handler'] in self.logger.handlers:
            # Check for the console handler and set its level to DEBUG to allow all logs to log through console 
            self.handlers['console_handler'].setLevel(logging.DEBUG)    
    
    
    # Disable console logging if it was enabled previously or default
    def disable_console_logging(self):
        self.log_to_console = False
        if self.handlers['console_handler'] in self.logger.handlers:
            # Check for the console handler and set its level to CRITICAL to only log to console if they are CRITICAL
            self.handlers['console_handler'].setLevel(logging.CRITICAL)
            
            
    # Remove a handler from the logger permanently
    def remove_handler(self, handler):
        # Deleting the handler from the handlers dictionary
        del self.handlers[handler]
        # Check if the handler is present in the logger's handlers
        for handler_ in self.logger.handlers:
            if handler_ == handler:
                # Remove the handler from the logger permanently
                self.logger.removeHandler(handler_)
                break
            
            
    # Custom log message function which logs the message through all the handlers, It then depends on the handler's level if the log message will pass through
    def log_message(self, log_level, message):
        # Validate the log level provided by the user
        log_level = log_level.upper()
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("Invalid log level. Expected one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

        # Mapping log levels to corresponding logging methods
        log_level_mapping = {
            'DEBUG': self.logger.debug,
            'INFO': self.logger.info,
            'WARNING': self.logger.warning,
            'ERROR': self.logger.error,
            'CRITICAL': self.logger.critical
        }

        # Log the message with the specified log level using the mapped logging method
        log_level_mapping[log_level](message)
        

    # Read and display the contents of the log file line by line
    def read_log_file(self):
        with open(self.log_file, 'r') as file:
            for line in file:
                line = line.strip()  # To remove any leading/trailing whitespace
                print(line)


    # Clear log file in case of unwanted log statements filling up the log file
    def clear_log_file(self):
        with open(self.log_file, 'w') as file:
            # Opening the file in 'w' mode truncates it, effectively clearing its contents.
            pass

# Initializing logger
logger = Logger('SpotifyAPI', f'{log_data_path}SpotifyAPI.log', log_to_console=False, debug_mode=False)

# The Spotify API Helper to manage tokens and authorization seemlessly
class SpotifyAPIHelper:
    def __init__(self) -> None:
        self.refresh_or_get_new_tokens()
    
    
    # A local server to catch the OAuth2 redirection when retrieving the auth token
    # Using keyword cls is just a measure to differentiate self from cls, any keyword can be used 
    @classmethod
    def start_local_server(cls):
        # Set the port number for the local server
        PORT = 8000

        # Use the built-in SimpleHTTPRequestHandler as the base handler
        Handler = http.server.SimpleHTTPRequestHandler

        # Create a custom handler by inheriting from SimpleHTTPRequestHandler
        class CustomHandler(Handler):
            # Override log_request method to disable logging of incoming requests
            def log_request(self, code='-', size='-'):
                pass

            # It handles the incoming redirection from the OAuth2 provider
            def do_GET(self):
                # Extract the URL when the user is redirected back after authorization
                redirected_url = self.path

                # Extract the authorization code from the URL
                auth_code = redirected_url.split('?code=')[1]
             
                logger.log_message('info', f"From {cls.start_local_server.__name__} : Authorization code captured successfully, Auth Code: {auth_code}")
                # Store the authorization code in the environment configuration
                cls.update_tokens(auth_code,access=False, refresh=False, auth=True)
             
                var = 1
                    
                # Respond to the user's browser with a success message
                # Try responding with the HTML file if it exists, otherwise respond with a success message
                try:
                    # Open and read the HTML file
                    with open(f'{spotify_data_path}/auth_page.html', 'rb') as file:
                        html_response = file.read()
                    
                    # Send the response with HTML content
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(html_response)
               
                # If file not found then respond with a simple success message
                except FileNotFoundError:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Authorization code captured successfully. You can now close this window.')
                    

        # Start the local web server on the specified port which listens for incoming connections.
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            # Print a message indicating that the server is running
            print("Local web server started on port", PORT)

            # Log that the server has started and is waiting for the authorization code
            logger.log_message('info', f'From {cls.start_local_server.__name__} : Local web server started. Waiting for the authorization code.')

            # Open the browser to initiate the OAuth2 authorization process
            cls.get_authorization_code()

            # Create a separate thread to handle incoming requests and wait with a timeout //refer documentation for explanation
            httpd_thread = threading.Thread(target=httpd.handle_request)
            httpd_thread.start()
            httpd_thread.join(timeout=30)  # Set the timeout to 30 seconds

            # If the thread is still alive after the timeout, handle the timeout
            if httpd_thread.is_alive():
                # Shut down the server
                httpd.shutdown()

                # Print a message indicating that the server request timed out
                print("Server request timed out.")

                # Log an error message about the server request timing out
                logger.log_message('error', f'From {cls.start_local_server.__name__} : Server request timed out.')

                # Return status_code 500 if the server request timed out
                return {
                    'status_code': 500
                }
            
            else:
                # Return status_code 200 if it's successfull
                return {
                    'status_code': 200,
                    'auth_code': auth_code
                }
                

    # To authorize a new user, provided the auth code should be valisd
    @classmethod
    def authorize_new_user(cls, auth_code=None):
        logger.log_message('debug', f'From {cls.authorize_new_user.__name__} : Authorizing new user')
        
        if auth_code is None:
            logger.log_message('debug', f'From {cls.authorize_new_user.__name__} : Auth code not passed, To get an auth code using method {cls.refresh_or_get_new_tokens.__name__}')
            cls.refresh_or_get_new_tokens()
            
            logger.log_message('info', f"From {cls.authorize_new_user.__name__} : New user authorized successfully, Returns True")
            return {
                    'status': 'success',
                    'user': SpotifyAPIUtility.get_current_user_profile() 
                    }
        
        else:
            logger.log_message('debug', f'From {cls.authorize_new_user.__name__} : Auth code passed, To get an access token using method {cls.get_access_and_refresh_tokens.__name__}')
            cls.update_tokens(auth_code,access=False, refresh=False, auth=True)
            
            # Now we can proceed to get the access token
            token = cls.get_access_and_refresh_tokens(auth_code=auth_code, redirect_uri=fast_redirect_uri)
            
            # There is another error occuring even after a valid auth code 
            if token.get('error') == 'invalid_grant':
                logger.log_message('error', f"From {cls.authorize_new_user.__name__} : While trying to register a new user {token.get('error_description')}")

            # If the error is inavlid_client
            elif token.get('error') == 'invalid_client':
                logger.log_message('error', f"From {cls.authorize_new_user.__name__} : Invalid client credentials.")
            
            # If the token is not returning an error, it means the tokens were successfully generated
            else:
                # Updating the env file with new tokens
                cls.update_tokens(token)
                logger.log_message('info', f"From {cls.authorize_new_user.__name__} : New user authorized successfully, Returns True")
                return {
                    'status': 'success',
                    'user': SpotifyAPIUtility.get_current_user_profile() 
                    }
            
            logger.log_message('info', f"From {cls.authorize_new_user.__name__} : New user authorization failed, Returns False")
            return {
                    'status': 'error'
                    }

    
    # A unified function which handles the fetching of tokens, if the access_token is expired, it will refresh the access_token through refresh_token
    # and if the refresh_token is expired it will get a new auth_token through authorization
    @classmethod
    def refresh_or_get_new_tokens(cls):
        global auth_code, refresh_token, access_token
        
        logger.log_message('debug',f'From {cls.refresh_or_get_new_tokens.__name__} : Refreshing or getting new tokens')
        
        # Try to refresh the access token only if the token values are not none:
        if auth_code and refresh_token:
            token = cls.refresh_access_token()
                
            # If refresh_access_token is returning an error, it means expired access token or invalid refresh token 
            if token.get('error') == 'invalid_grant':  
                logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : Refresh token is invalid or expired. Need to get new authorization code.")
                
                # Getting new tokens, first we have to renew auth code
                # Start the local web server to capture the authorization code
                response = cls.start_local_server()

                # Checking if the auth code fetching was successfull
                if response['status_code'] == 200:
                    
                    # Now we can proceed to get the access token
                    token = cls.get_access_and_refresh_tokens()
                    
                    # There is another error occuring even after a valid auth code 
                    if token.get('error') == 'invalid_grant':
                        logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : From code block 1 trying after fetching auth code {token.get('error_description')}")

                    # If the error is inavlid_client
                    elif token.get('error') == 'invalid_client':
                        logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : Invalid client credentials.")
                    
                    # If the token is not returning an error, it means the tokens were successfully generated
                    else:
                        # Updating the env file with new tokens
                        cls.update_tokens(token)
                
                # If the status_code was not 200, it means the local server request timed out
                elif response['status_code'] == 500:
                    logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : Local server request timed out.")
                
                # Unexpected error occured 
                else:
                    logger.log_message('warning', f"From {cls.refresh_or_get_new_tokens.__name__} : Unexpected error occured")
                    
            # If invalid client
            elif token.get('error') == 'invalid_client':
                logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : Invalid client credentials.")
                
            # refresh_access_token is returning a valid token, means the fetch was successfull 
            else:
                # Updating the env file with new access token
                cls.update_tokens(token, refresh=False)
        
        # If token or auth code values are none refreshing everything to avoid errors 
        elif not auth_code or not refresh_token:
            
            # Getting auth code
            response = cls.start_local_server()
            
            # Checking if the auth code fetching was successfull
            if response.get('status_code') == 200:
                
                # Now we can proceed to get the tokens
                token = cls.get_access_and_refresh_tokens()
                
                # There is another error occuring even after a valid auth code 
                if token.get('error') == 'invalid_grant':
                    logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : {token.get('error_description')}")
            
                # If the token is not returning an error, it means the tokens were successfully generated
                else:
                    # Updating the env file with new tokens
                    cls.update_tokens(token)
            
            # If the status_code was not 200, it means the local server request timed out
            elif response.get('status_code') == 500:
                logger.log_message('error', f"From {cls.refresh_or_get_new_tokens.__name__} : Local server request timed out.")
            
            # Unexpected error occured 
            else:
                logger.log_message('warning', f"From {cls.refresh_or_get_new_tokens.__name__} : Unexpected error occured")
                
        
    # To get the authorization code by opening the browser and redirecting the user to the spotify authorization page
    @classmethod
    def get_authorization_code(cls):
        url = get_auth_code_url
        headers = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': scope
        }
        post_url = url + urlencode(headers)
        # Open the browser with the post method to the authorization page
        webbrowser.open(post_url)
    
    
    # To get the authorization url
    @classmethod
    def get_authorization_url(cls, custom_redirect_uri=None, custom_scope = None):
        
        custom_scope = custom_scope if custom_scope else scope
        
        if custom_redirect_uri:
            current_redirect_uri = custom_redirect_uri
        else:
            current_redirect_uri = redirect_uri
        
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Getting authorization url')
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Redirect uri : {current_redirect_uri}')
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Scope : {scope}')
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Client id : {client_id}')
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Client secret : {client_secret}')
        
        url = get_auth_code_url
        headers = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': current_redirect_uri,
            'scope': custom_scope
        }
        post_url = url + urlencode(headers)
        
        logger.log_message('debug', f'From {cls.get_authorization_url.__name__} : Auth code url : {post_url}')
        return post_url

    
    # To get the access token and refersh token from the authorization code
    @classmethod
    def get_access_and_refresh_tokens(cls, auth_code=None, redirect_uri=None):
        
        auth_code = auth_code if auth_code else os.getenv('AUTHORIZATION_CODE')
        redirect_uri = redirect_uri if redirect_uri else os.getenv('REDIRECT_URI')
        
        logger.log_message('debug', f'From {cls.get_access_and_refresh_tokens.__name__} Sending Tokens, Params: auth_code: {auth_code}, redirect_uri: {redirect_uri}')
        
        response = requests.post(
            get_access_token_url,
            data={
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            },
            headers={
                'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('utf-8')).decode('utf-8')
            }
        )
        
        # If the response is 200, it means the token was successfully generated
        if response.status_code == 200:
            json_resp = response.json()
            access_token = json_resp['access_token']
            refresh_token = json_resp['refresh_token']
            
            # Return the token values
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'error': None
            }
        
        # If the response is not 200, it means the token was not successfully generated
        else:
            response_dict = json.loads(response.text)
            # Return the response for the calling function to handle the error
            return response_dict


    # To refresh the access token through refresh token
    @classmethod
    def refresh_access_token(cls):
        response = requests.post(
            get_access_token_url,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            },
            headers={
                'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('ascii')).decode('ascii')
            }
        )

        # If the response is 200, it means the access token was successfully refreshed
        if response.status_code == 200:
            resp_json = response.json()
            access_token = resp_json['access_token']
            return {
                'access_token': access_token,
                'error': None
                    }
            
        # If the response is not 200, it means that there was an error in refreshing the access token
        else:
            response_dict = json.loads(response.text)
            # Return the response for the calling function to handle the error
            return response_dict


    # To update the access token and refresh token in the env file
    @classmethod
    def update_tokens(cls, token, access=True, refresh=True, auth=False):
        global auth_code, access_token, refresh_token, expires_in
        
        if token:
            # If instructions are to set access token then update it
            if access:
                access_token = token['access_token']
                # Setting the expiry time of the access token to be 3600 seconds (1 hour) from now
                
                expires_in = time.perf_counter() + 3600
                logger.log_message('info', f'{"From " + cls.update_tokens.__name__} : Access token is set.')
                
                set_key(env_file, 'ACCESS_TOKEN', access_token)
            
            # If instructions are to set refresh token then update it
            if refresh:
                refresh_token = token['refresh_token']
                logger.log_message('info', f'{"From " + cls.update_tokens.__name__} : Refresh token is set.')
                set_key(env_file, 'REFRESH_TOKEN', refresh_token) 

            if auth:
                auth_code = token
                logger.log_message('info', f'{"From " + cls.update_tokens.__name__} : Authorization code is set.')
                set_key(env_file, 'AUTHORIZATION_CODE', auth_code)


    # To retrieve the any variable from the env file in real time
    @classmethod
    def get_access_token(cls):
        if cls.is_access_token_expired():
            cls.refresh_or_get_new_tokens()
            return access_token
        else:
            return access_token
    

    # To check if the access token is expired
    @classmethod
    def is_access_token_expired(cls):
        return (time.perf_counter() > expires_in)
        

class SpotifyAPIUtility:
    
    # To get current users profile
    @classmethod
    def get_current_user_profile(cls, access_token=None):
        global user_id, user_name
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token()
        
        # Sending a get request to get the current user's profile
        logger.log_message('info', f"{'From ' + cls.get_current_user_profile.__name__} : Retrieving user's profile")    
        response = requests.get(
            get_current_user_profile_url,
            headers={'Authorization': f"Bearer {access_token}"}
        )

        # If the status_code is 200, means the method was successful
        if response.status_code == 200:
            logger.log_message('info', "Successfully retrieved user's profile")
            json_resp = response.json()
            
            user_id = json_resp['id']
            user_name = json_resp['display_name']

            user = {
                'user_id' : user_id,
                'user_name' : user_name
            }
            
            # Updating the environment variables with the user's id and name
            set_key(env_file, 'USER_ID', user_id)
            set_key(env_file, 'USER_NAME', user_name)
            
            logger.log_message('info', f"From {cls.get_current_user_profile.__name__} : Updated environment variables with user's id and name")
            
            return user
            
        # If the status code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', json_resp['error']['message'])
        
        # If some other error occurs
        else:
            # json_resp = response.json()
            logger.log_message('error', f"From {cls.get_current_user_profile.__name__} : Status code: {response.status_code} Error: {response.text}")
    
    # To get all the playlists of the user
    @classmethod
    def get_user_playlists(cls, access_token=None, user_id=None):
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token()
        user_id = user_id if user_id else SpotifyAPIUtility.get_user_id()
    
        # Sending a get request to get the user's playlists
        logger.log_message('info', f"{'From ' + SpotifyAPIUtility.get_user_playlists.__name__} : Retrieving user's playlists")
        response = requests.get(
            get_user_playlists_url.format(user_id=user_id),
            headers={'Authorization': f"Bearer {access_token}"},
            params={
                'limit':50
            }
        )

        # If the status_code is 200, means the method was successful
        if response.status_code == 200:
            logger.log_message('info', "Successfully retrieved user's playlists")
            json_resp = response.json()

            # Returning the playlists
            playlists = []
            for item in json_resp["items"]:
                try:
                    playlist = {
                    'href': item['href'],
                    'id': item['id'],
                    'uri': item['uri'],
                    'images': item['images'],
                    'image': item['images'][0]['url'],
                    'description': item['description'],
                    'name': item['name'],
                    'tracks': item['tracks']
                    }
                except:
                    print(item['id'])
                playlists.append(playlist)
              
            # print(len(playlists))
                
            return playlists

        # If the status code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.get_user_playlists.__name__} : Error : {json_resp['error']['message']}")
        
            # Return None
            return ''
        
        # If some other error occurs
        else:
            print(response.status_code)
            print(response.text)
            print
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.get_user_playlists.__name__} : Status code: {response.status_code} Error: {json_resp['error']['message']}")
        
            return ''
            
    
    # To get the tracks of the playlist
    @classmethod
    def get_playlist_tracks(cls, access_token=None, playlist_id=None):
        if playlist_id is None:
            logger.log_message('error', f"From {SpotifyAPIUtility.get_playlist_tracks.__name__} : Error : playlist_id is None")
            return ''
        
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token()
    
        # Sending a get request to get the user's playlists
        logger.log_message('info', f"{'From ' + SpotifyAPIUtility.get_playlist_tracks.__name__} : Retrieving user's tracks")
        response = requests.get(
            get_playlist_tracks_url.format(playlist_id=playlist_id),
            headers={'Authorization': f"Bearer {access_token}"},
            params={
                'limit':50
            }
        )

        # If the status_code is 200, means the method was successful
        if response.status_code == 200:
            logger.log_message('info', "Successfully retrieved playlist's tracks")
            json_resp = response.json()

            # Returning the tracks
            tracks = []
            for item in json_resp["items"]:
                item = item["track"]
                track = {
                'href': item['href'],
                'id': item['id'],
                'uri': item['uri'],
                'name': item['name'],
                'artists': ','.join([artist['name'] for artist in item['artists']]),
                }
                tracks.append(track)
              
            return tracks

        # If the status code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.get_playlist_tracks.__name__} : Error : {json_resp['error']['message']}")
        
            # Return None
            return ''
        
        # If some other error occurs
        else:
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.get_playlist_tracks.__name__} : Status code: {response.status_code} Error: {response.text}")
        
            return ''


    # A method to get user_id
    @classmethod
    def get_user_id(cls):
        global user_id
        if user_id:
            return user_id
        else:
            SpotifyAPIUtility.get_current_user_profile()
            return user_id
        

    # To get the recommendations (in form of tracks) from the spotify api
    @staticmethod         
    def get_recommendations_spotify(parameters,access_token=None):
        # Refer to documentation for @staticmethod usecase  
        
        
            # params = {
        #     'limit': int,
        #     'seed_genres': list,
        #     'seed_artist': list,
        #     'seed_tracks': list,
        #     'target_acousticness' : float,
        #     'target_danceability' : float,
        #     'target_instrumentalness' : float,
        #     'target_energy' : float,
        # }
        
        # @param access_token: The access token to be used to get the playlists
        # @param limit: The number of songs to be returned
        # @param seed_genres: The list of genres to be used as a seed
        # @param seed_artist: The list of artists to be used as a seed
        # @param seed_tracks: The list of tracks to be used as a seed
        # @param target_acousticness: The target acousticness to be used as a filter
        # @param target_danceability: The target danceability to be used as a filter
        # @param target_instrumentalness: The target instrumentalness to be used as a filter
        # @param target_energy: The target energy to be used as a filter
        
        # Note: Total sum of number of seed_genres, seed_artist and seed_tracks should not be greater than 5  
        
        # @return: The array of tracks to be returned
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token() 
        # Sending a get request to get tracks
        response = requests.get(
            get_recommendations_url,
            headers={
                'Authorization': f'Bearer {access_token}' 
            }, 
            params=parameters
        )
        
        # If the status_code is 200, means the method was successful
        if response.status_code == 200:
            logger.log_message('info', f'{"From " + SpotifyAPIUtility.get_recommendations_spotify.__name__} :Successfully retrieved recommendations playlists')
            json_resp = response.json()
            # Retrieving tracks from the json response
            playlist = []
            
            for track in json_resp['tracks']:
                track = {
                    'track_name': track['name'],
                    'track_id': track['id'],
                    'track_uri': track['uri'],
                    'track_populalrity': track['popularity'],
                    'artists': [{'artist_name' : artist['name'], 'artist_id': artist['id']} for artist in track['artists']]                
                }
                playlist.append(track)
            
            # Returning the array of tracks
            return playlist
             
        # If the status_code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', f'{"From " + SpotifyAPIUtility.get_recommendations_spotify.__name__} : {json_resp["error"]["message"]}')
            
            # Return an empty array
            return []
        
        # If the status_code is not 200 or 401, means unexpected error
        else:
            json_resp = response.json()
            logger.log_message('error', f'{"From " + SpotifyAPIUtility.get_recommendations_spotify.__name__} : Status code: {response.status_code} Error: {json_resp["error"]["message"]}')            
            
            # Return an empty array
            return []
        
    
    # To create a playlist of the recommended songs
    @staticmethod
    def create_playlist_spotify(playlist_name, description, user_id=None, access_token=None):
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token()
        user_id = user_id if user_id else SpotifyAPIUtility.get_user_id()
        
        logger.log_message('info', f"From {SpotifyAPIUtility.create_playlist_spotify.__name__} : Creating playlist")
        # Sending a post request to create a playlist
        response = requests.post(
            create_playlist_url.format(user_id=user_id),
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type' : 'application/json'
            }, 
            json={
                'name': playlist_name,
                'description': description,
                'public': True
            }
        )
        
        # If the status_code is 201, means the method was successful
        if response.status_code == 201:
            json_resp = response.json()
            
            logger.log_message('info', f"From {SpotifyAPIUtility.create_playlist_spotify.__name__} : Successfully created playlist, playlist_id : {json_resp['id']}")
            
            # Returning the playlist id
            return {
                'playlist_id': json_resp['id'],
                'playlist_url': json_resp['external_urls']['spotify'],
                'playlist_uri': json_resp['uri']
            }
        
        # If the status code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.create_playlist_spotify.__name__} : Error : {json_resp['error']['message']}")
        
            # Return None
            return ''
        
        # If some other error occurs
        else:
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.create_playlist_spotify.__name__} : Status code: {response.status_code} Error: {json_resp['error']['message']}")
        
            return ''
        
   
    # To add itmes to a playlist
    @staticmethod
    def add_items_to_spotify_playlist(playlist_id, track_uris, access_token=None):
        access_token = access_token if access_token else SpotifyAPIHelper.get_access_token()
        
        # Sending a post request to add items to a playlist
        logger.log_message('info', f"From {SpotifyAPIUtility.add_items_to_spotify_playlist.__name__} : Adding items to a playlist")
        response = requests.post(
            edit_items_in_playlist_url.format(playlist_id=playlist_id),
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type' : 'application/json'
            },
            json={
                'uris': track_uris,
                'position': 0,
            }
        )
        
        # If the status_code is 201, means the method was successful
        if response.status_code == 201:
            json_resp = response.json()
            
            logger.log_message('info', f"From {SpotifyAPIUtility.add_items_to_spotify_playlist.__name__} : Successfully added items to a playlist, snapshot_id: {json_resp['snapshot_id']}")
            
            # Returning the playlist id
            return json_resp['snapshot_id']
        
        # If the status code is 401, means bad or expired access token
        elif response.status_code == 401:
            # Invalid access token
            json_resp = response.json()
            logger.log_message('error', f'{"From " + SpotifyAPIUtility.add_items_to_spotify_playlist.__name__} : {json_resp["error"]["message"]}')
        
            # Return None 
            return ''
        
        # If some other error occurs
        else:
            json_resp = response.json()
            logger.log_message('error', f"From {SpotifyAPIUtility.add_items_to_spotify_playlist.__name__} : Status code: {response.status_code} Error: {json_resp['error']['message']}")
        
            return ''
        
        
    # A unified method to include create playlist and adding items to the playlist
    @classmethod
    def create_and_add_to_playlist(cls, parameters):
        
        logger.log_message('info', f"From {cls.create_and_add_to_playlist.__name__} : Creating and adding items to a playlist")

        # First create the playlist
        created_playlist = cls.create_playlist_spotify(parameters['playlist_name'],parameters['playlist_description'])
        
        # Check if the playlist_id is not empty
        if created_playlist['playlist_id']:
            parameters['playlist_id'] = created_playlist['playlist_id']
            parameters['playlist_url'] = created_playlist['playlist_url']
            parameters['playlist_uri'] = created_playlist['playlist_uri']

            # Then add the items to the playlist
            parameters['snapshot_id'] = cls.add_items_to_spotify_playlist(parameters['playlist_id'], parameters['track_uris'])
            
            # Check if the add items was successfull by checking if the snapshot_id is not empty
            if parameters['snapshot_id']:
                logger.log_message('info', f"From {cls.create_and_add_to_playlist.__name__} : Successfully created and added items to a playlist")
                
                return {
                    'playlist_id': parameters['playlist_id'],
                    'playlist_url': parameters['playlist_url'],
                    'playlist_uri': parameters['playlist_uri'],
                    'snapshot_id': parameters['snapshot_id'],
                    'is_playlist_created': True,
                }
            
            # If the snapshot_id is empty, means the add items was not successfull
            else:
                logger.log_message('error', f"From {cls.create_and_add_to_playlist.__name__} : Failed to add items to a playlist")
                
                return {
                    'is_playlist_created': False,
                }
                
        # If the playlist_id is not returned
        else:
            logger.log_message('error', f"From {cls.create_and_add_to_playlist.__name__} : Failed to create playlist")            
            
            return {
                'is_playlist_created': False,
            }
            
        
if __name__ == '__main__':
    logger = Logger('SpotifyAPI', f'{log_data_path}SpotifyAPI.log', log_to_console=False, debug_mode=False)
    SAI = SpotifyAPIUtility
    SAH = SpotifyAPIHelper
    SAH.authorize_new_user()
    print(SAI.get_user_playlists())
