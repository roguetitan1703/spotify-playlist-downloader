
import os, sys
project_root = os.getcwd()
sys.path.append(project_root)
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/packages')
# print(sys.path)

# Adding the project's root directory to the path

# Import local modules
from packages.Spotify_.SpotifyAPI import SpotifyAPIUtility
from packages.json_helper.json_helper import dump_file, read_file
# Initialising the paths for data files
playlist_file = f'{project_root}/data/Spotify_/playlists.json'
genre_feature_aggregate = f'{project_root}/data/tracks_dataset/genre_stats.json'

# To save the playlists details locally
def save_playlist(playlist):
    # Fetching already saved playlist details if any
    playlists = read_file(playlist_file)
    
    # Checking if playlist details are already there
    if playlists:
        playlists.append(playlist)
    # If not then creating a new list and adding the playlist details
    else:
        playlists = [playlist]
        
    # Saving the details into the files
    dump_file(playlist_file, playlists)
    
# Function to tweek the target ranges in refrence with the max and min values to the specific genre
def tweek_target_ranges(genre, target, value):
    # Fetching genre specific features aggregates
    genre_feature_agg = read_file(genre_feature_aggregate)[genre.lower()]
    
    # Fetching the max and min values of the genre
    max_value = genre_feature_agg[target]['max']
    min_value = genre_feature_agg[target]['min']
    
    # Calculating the tweeked value
    # print(type(max_value), type(min_value), type(value))
    
    tweeked_value = (max_value - min_value) * (value) + min_value
    
    return tweeked_value
    
    
# Get the recommendation tracks with the SpotifyAPIGetRecommendations method get_recommendations_spotify
def make_recommendation_playlist(recommendation_parameters):
            
    # Filtering and tweeking the parameters
    # Acousticness
    if recommendation_parameters['target_acousticness'] == 0.0:
        del recommendation_parameters['target_acousticness']
    else:
        recommendation_parameters['target_acousticness'] = tweek_target_ranges(recommendation_parameters['seed_genres'].lower(), 'acousticness', recommendation_parameters['target_acousticness'])
    
    # Speechiness
    if recommendation_parameters['target_speechiness'] == 0.0:
        del recommendation_parameters['target_speechiness']
    else:
        recommendation_parameters['target_speechiness'] = tweek_target_ranges(recommendation_parameters['seed_genres'].lower(), 'speechiness', recommendation_parameters['target_speechiness'])
        
    # Danceability
    if recommendation_parameters['target_danceability'] == 0.0:
        del recommendation_parameters['target_danceability']
    else:
        recommendation_parameters['target_danceability'] = tweek_target_ranges(recommendation_parameters['seed_genres'].lower(), 'danceability', recommendation_parameters['target_danceability'])
    
    # Instrumentalness
    if recommendation_parameters['target_instrumentalness'] == 0.0:
        del recommendation_parameters['target_instrumentalness']
    else:
        recommendation_parameters['target_instrumentalness'] = tweek_target_ranges(recommendation_parameters['seed_genres'].lower(), 'instrumentalness', recommendation_parameters['target_instrumentalness'])
        
    # Energy
    if recommendation_parameters['target_energy'] == 0.0:
        del recommendation_parameters['target_energy']
    else:
        recommendation_parameters['target_energy'] = tweek_target_ranges(recommendation_parameters['seed_genres'].lower(), 'energy', recommendation_parameters['target_energy'])
        
                
    # Get the playlist from the get_recommendation_spotify method
    print(recommendation_parameters)
    tracks_array = SpotifyAPIUtility.get_recommendations_spotify(parameters=recommendation_parameters)
    
    # If the tracks array is not empty
    if tracks_array:
    
        # Make the track_uris array which contains uri of all the tracks in the playlist
        # R// refer the function SpotifyAPIUtility.get_recommendation_spotify() for the format of the data stored in the array playlist 
        playlist_creation_parameters = {
                'playlist_name' : f"{recommendation_parameters['seed_genres']} Playlist",
                'playlist_description' : f"This is a playlist of {recommendation_parameters['seed_genres']} songs created by Personalised Music Discovery Project",
                'track_uris' : [track['track_uri'] for track in tracks_array]
        }
        
        # Create a playlist in the user's Spotify account
        created_playlist = SpotifyAPIUtility.create_and_add_to_playlist(parameters=playlist_creation_parameters)
        
        if created_playlist['is_playlist_created']:
            # Save the playlist details locally
            save_playlist(created_playlist)      
            # print(recommendation_parameters)
                
            return created_playlist
                
        else:
            return {'error': 'Playlist creation failed'}

    # If it's empty
    else:
        return {'error': 'No tracks found'}


def embedd_playlist(playlist_id):
    embedd_html = f"""<iframe style="border-radius:12px" src="https://open.spotify.com/embed/playlist/{playlist_id}?utm_source=generator" width="100%" height="100%" frameborder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>"""
    return embedd_html


if __name__ == '__main__':
    print(tweek_target_ranges('rock', 'energy', 0.5))