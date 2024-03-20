import os, sys, random, string
from ytmusicapi import YTMusic
from pytube import YouTube
from pydub import AudioSegment

project_root = os.getcwd()
sys.path.append(f"{project_root}/modules")
youtube_data_path = f'{project_root}/data/Youtube'
AUDIO_DOWNLOAD_DIR = f'{youtube_data_path}/audio'

ytmusic = YTMusic(f'{youtube_data_path}/oauth.json')


class YoutubeAPIHelper:
    
    @staticmethod
    def get_track_url(track):
        '''   track = {
        'href': item['href'],
        'id': item['id'],
        'uri': item['uri'],
        'name': item['name'],
        'artists': ','.join([artist['name'] for artist in item['artists']]),
        }'''

        query = f"{track['name']} {track['artists']}"
        
        results = ytmusic.search(query, filter="songs", limit=1)
        if results:
            return f"https://youtu.be/{results[0]['videoId']}"
        else:
            return None
      
      
    @staticmethod   
    def get_tracks_url_by_batch(tracks):
        return [YoutubeAPIHelper.get_track_url(track) for track in tracks]


    @staticmethod
    def download_track_by_url(track_url, DOWNLOAD_DIR):
        video = YouTube(track_url)
        video_stream = video.streams.filter(only_audio = True).first()

        # try:
          
        video_stream.download(f"{DOWNLOAD_DIR}")
        
        # Convert to MP3 with 320 kbps bitrate
        mp3_file_path = os.path.join(DOWNLOAD_DIR, f"{video.title}.mp3")
        print(mp3_file_path)
        print(f"{DOWNLOAD_DIR}/{video_stream.default_filename}")
        audio = AudioSegment.from_file(f"{DOWNLOAD_DIR}/{video_stream.default_filename}")
        
        # Set the desired audio bitrate to 320 kbps
        audio = audio.set_frame_rate(48000).set_channels(2).set_sample_width(2)

        # Export the MP3 file
        audio.export(mp3_file_path, format="mp3", bitrate="320k")
        
        # Clean up: delete the downloaded video and converted MP3
        os.remove(video_stream.default_filename)
        
        print("audio was downloaded successfully")  

        # except Exception as e:
        #     print("Failed to download audio")
        #     print(f"An error occurred: {type(e).__name__}: {e}")
        #     # Print additional details if available
        #     if hasattr(e, 'args'):
        #         print(f"Error details: {e.args}")

        
    @staticmethod
    def download_tracks_by_batch(tracks_url,DOWNLOAD_DIR=''):
        DOWNLOAD_DIR = DOWNLOAD_DIR if DOWNLOAD_DIR else f"{AUDIO_DOWNLOAD_DIR}/{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))}"
        
        for track_url in tracks_url:
            YoutubeAPIHelper.download_track_by_url(track_url,DOWNLOAD_DIR)
            
        return DOWNLOAD_DIR
 


if __name__ == "__main__":
    tracks = [{'artists': 'Arctic Monkeys',
    'href': 'https://api.spotify.com/v1/tracks/0BxE4FqsDD1Ot4YuBXwAPp',
    'id': '0BxE4FqsDD1Ot4YuBXwAPp',
    'name': '505',
    'uri': 'spotify:track:0BxE4FqsDD1Ot4YuBXwAPp'},
    {'artists': 'The Neighbourhood',
    'href': 'https://api.spotify.com/v1/tracks/2QjOHCTQ1Jl3zawyYOpxh6',
    'id': '2QjOHCTQ1Jl3zawyYOpxh6',
    'name': 'Sweater Weather',
    'uri': 'spotify:track:2QjOHCTQ1Jl3zawyYOpxh6'},
    {'artists': 'Arctic Monkeys',
    'href': 'https://api.spotify.com/v1/tracks/5XeFesFbtLpXzIVDNQP22n',
    'id': '5XeFesFbtLpXzIVDNQP22n',
    'name': 'I Wanna Be Yours',
    'uri': 'spotify:track:5XeFesFbtLpXzIVDNQP22n'},
    {'artists': 'The Neighbourhood',
    'href': 'https://api.spotify.com/v1/tracks/2K7xn816oNHJZ0aVqdQsha',
    'id': '2K7xn816oNHJZ0aVqdQsha',
    'name': 'Softcore',
    'uri': 'spotify:track:2K7xn816oNHJZ0aVqdQsha'},
    {'artists': 'The Weeknd',
    'href': 'https://api.spotify.com/v1/tracks/2LBqCSwhJGcFQeTHMVGwy3',
    'id': '2LBqCSwhJGcFQeTHMVGwy3',
    'name': 'Die For You',
    'uri': 'spotify:track:2LBqCSwhJGcFQeTHMVGwy3'},
    {'artists': 'The Neighbourhood',
    'href': 'https://api.spotify.com/v1/tracks/2xql0pid3EUwW38AsywxhV',
    'id': '2xql0pid3EUwW38AsywxhV',
    'name': 'Reflections',
    'uri': 'spotify:track:2xql0pid3EUwW38AsywxhV'},
    {'artists': 'The Weeknd',
    'href': 'https://api.spotify.com/v1/tracks/2p8IUWQDrpjuFltbdgLOag',
    'id': '2p8IUWQDrpjuFltbdgLOag',
    'name': 'After Hours',
    'uri': 'spotify:track:2p8IUWQDrpjuFltbdgLOag'},
    {'artists': 'Mr.Kitty',
    'href': 'https://api.spotify.com/v1/tracks/2LKOHdMsL0K9KwcPRlJK2v',
    'id': '2LKOHdMsL0K9KwcPRlJK2v',
    'name': 'After Dark',
    'uri': 'spotify:track:2LKOHdMsL0K9KwcPRlJK2v'},
    {'artists': 'd4vd',
    'href': 'https://api.spotify.com/v1/tracks/1xK59OXxi2TAAAbmZK0kBL',
    'id': '1xK59OXxi2TAAAbmZK0kBL',
    'name': 'Romantic Homicide',
    'uri': 'spotify:track:1xK59OXxi2TAAAbmZK0kBL'},
    {'artists': 'Tory Lanez',
    'href': 'https://api.spotify.com/v1/tracks/3azJifCSqg9fRij2yKIbWz',
    'id': '3azJifCSqg9fRij2yKIbWz',
    'name': 'The Color Violet',
    'uri': 'spotify:track:3azJifCSqg9fRij2yKIbWz'},
    {'artists': 'LonelyEve',
    'href': 'https://api.spotify.com/v1/tracks/5qpXZ45eZA3VX3qe76tmqh',
    'id': '5qpXZ45eZA3VX3qe76tmqh',
    'name': 'The Hills X Creepin X The Color Violet',
    'uri': 'spotify:track:5qpXZ45eZA3VX3qe76tmqh'}]
    
    tracks_url = YoutubeAPIHelper.get_tracks_url_by_batch(tracks)
    print(tracks_url)
    # download them
    YoutubeAPIHelper.download_tracks_by_batch(tracks_url)