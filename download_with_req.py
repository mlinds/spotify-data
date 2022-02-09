#%%
import logging

import pandas as pd
import requests_cache
from spotipy.oauth2 import SpotifyOAuth

from secret_vars import CLIENT_ID, CLIENT_SECRET

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def get_auth_token():
    """
    Based on the scope and the user vars, and Auth token is returned for later use
    """
    scope = "user-library-read,playlist-read-private,user-top-read,user-read-recently-played"
    manager = SpotifyOAuth(
        scope=scope,
        username="maelinds",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://localhost:7777/callback",
    )

    return manager.get_access_token(as_dict=False)


token = get_auth_token()

PREFIX = "https://api.spotify.com/v1/"


def parse_library_json(api_return):
    """[summary]

    Args:
        api_return (json-formatted string): The Response from the Spotify API

    Yields:
        dict: Dictionary of the relevant data
    """
    for item in api_return["items"]:
        songdata = {
            "name": item["track"]["name"],
            "popularity": item["track"]["popularity"],
            "albumName": item["track"]["album"]["name"],
            "artistNames": item["track"]["artists"][0]["name"],
            "spotifyUri": item["track"]["uri"],
        }

        yield songdata


def parse_top_tracks_json(api_return):
    """
    Parse the API response when requesting top tracks

    Args:
        api_return (str): JSON formatted Spotify API response string

    Yields:
        [type]: [description]
    """
    for item in api_return["items"]:
        songdata = {
            "name": item["name"],
            "popularity": item["popularity"],
            "albumName": item["album"]["name"],
            "artistNames": item["artists"][0]["name"],
            "spotifyUri": item["uri"],
        }

        yield songdata


def parse_recent_tracks_json(api_return):
    """[summary]

    Args:
        api_return ([type]): [description]

    Yields:
        [type]: [description]
    """
    for item in api_return["items"]:
        songdata = {
            "name": item["track"]["name"],
            "popularity": item["track"]["popularity"],
            "albumName": item["track"]["album"]["name"],
            "artistNames": item["track"]["artists"][0]["name"],
            "spotifyUri": item["track"]["uri"],
            "timePlayed": item["played_at"],
        }

        yield songdata


def generic_download(url, parse_func, csv_out):
    """[summary]

    Args:
        url ([type]): [description]
        parse_func ([type]): [description]
        csv_out ([type]): [description]
    """
    with requests_cache.CachedSession("spotify_cache") as session:

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # hit the endpoint once to get the first 'next' url
        request = session.get(PREFIX + url, headers=headers)

        df = pd.DataFrame(parse_func(request.json()))

        while request.status_code == 200:
            next_url = request.json()["next"]
            if next_url is None:
                break
            logger.debug("Requesting data from %s" % next_url)
            request = session.get(next_url, headers=headers)
            logger.debug("Request Status:%s" % request.status_code)
            temp_df = pd.DataFrame(parse_func(request.json()))
            df = pd.concat([df, temp_df], ignore_index=True)

        df.to_csv(csv_out)


def download_tracks():
    url = "me/tracks"
    csv_path = "./data_out/all_tracks.csv"
    parse_func = parse_library_json
    
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)

def download_recent_top(time_range):
    url = f"me/top/tracks?time_range={time_range}_term"
    csv_path = f"./data_out/top_tracks_{time_range}.csv"
    parse_func = parse_top_tracks_json
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)


# %%
def download_recent():
    url = "me/player/recently-played?limit=10"
    csv_path = "./data_out/recent.csv"
    parse_func = parse_recent_tracks_json
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)
        


#%%~
if __name__ == "__main__":

    download_tracks()

    download_recent_top("short")
    download_recent_top("medium")
    download_recent_top("long")
    
    download_recent()

# %%
