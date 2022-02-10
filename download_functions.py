import logging
from datetime import timedelta

import pandas as pd
import requests_cache
from spotipy.oauth2 import SpotifyOAuth

try:
    from secret_vars import CLIENT_ID, CLIENT_SECRET
except ImportError:
    # for use in github actions workflow
    import os
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')


logging.basicConfig(filename='sp_api.log',level=logging.INFO,filemode='w')
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
    """
    Used for getting the all tracks from a library

    Args:
        api_return (list): List of JSON-formatted strings

    Yields:
        dict: Dictionary of the relevant data for each track
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
        api_return (list): List of JSON-formatted strings

    Yields:
        dict: Dictionary of the relevant data for each track
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
        api_return (list): List of JSON-formatted strings

    Yields:
        dict: Dictionary of the relevant data for each track
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

def request_logging(func):
    def wrapper(requrl,reqheaders):
        logger.info("Requesting data from %s", requrl)
        response = func(requrl,reqheaders)
        logger.info("Spotify API Request Status:%s", response.status_code)
        logger.debug('request: '+str(response.request.headers))
        logger.debug('response:',response.headers)
        logger.info('From cache: %s',str(response.from_cache))
        logger.info('Cache expires at: %s',response.expires)
    return wrapper

def generic_download(url, parse_func, csv_out):
    """Queries the Spotify API, parses the resonse, and saves it as a csv formatted file

    Args:
        url (str): Spotify REST endpoint of interest
        parse_func (func): A function to parse the list of JSON strings
        csv_out (path-line): where to store the CSV
    """
    with requests_cache.CachedSession("spotify_cache",
    backend='sqlite',
    cache_control=True,
    match_headers=True,
    # ignored_parameters="Authorization",
    expire_after=120) as session:

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # hit the endpoint once to get the first 'next' url
        logger.info("Requesting data from %s", PREFIX + url)
        response = session.get(PREFIX + url, headers=headers)
        logger.info("Spotify API Request Status:%s", response.status_code)
        logger.debug('request: ',response.request.headers)
        logger.debug('response:',response.headers)
        logger.info('From cache: %s',str(response.from_cache))
        logger.info('Cache expires at: %s',response.expires)
        # initialize df using appropriate parser
        df = pd.DataFrame(parse_func(response.json()))

        # loop over the differenet pages provided by the spotify API pagination
        while response.status_code == 200:
            next_url = response.json()["next"]
            if next_url is None:
                break
            logger.info("Requesting data from %s", next_url)
            response = session.get(next_url, headers=headers)
            logger.debug(response.headers)
            logger.debug(response.request.headers)
            logger.info('Cache expires at: %s',response.expires)
            logger.info("Spotify API Request Status:%s", response.status_code)
            logger.info('From cache: %s',str(response.from_cache))

            temp_df = pd.DataFrame(parse_func(response.json()))
            df = pd.concat([df, temp_df], ignore_index=True)

        df.to_csv(csv_out, index=None)
        logger.info('CSV data saved to %s',csv_out)


def download_library_tracks():
    """Download all library tracks"""
    url = "me/tracks"
    csv_path = "./data_out/all_tracks.csv"
    parse_func = parse_library_json
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)


def download_recent_top(time_range):
    """Downloads the top tracks in a certain time range

    Args:
        time_range (str): Based on the spotify API, either short, medium or long
    """
    url = f"me/top/tracks?time_range={time_range}_term"
    csv_path = f"./data_out/top_tracks_{time_range}.csv"
    parse_func = parse_top_tracks_json
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)


def download_recent_streams():
    """Download the most recent streams"""
    url = "me/player/recently-played?limit=10"
    csv_path = "./data_out/recent.csv"
    parse_func = parse_recent_tracks_json
    generic_download(url=url, parse_func=parse_func, csv_out=csv_path)


def append_recent_streams():
    download_recent_streams()
    all_stream_df = pd.read_csv("./data_out/streamHistory.csv")
    to_append = pd.read_csv("./data_out/recent.csv")
    pd.concat([all_stream_df, to_append]).drop_duplicates().sort_values('timePlayed').to_csv(
        "./data_out/streamHistory.csv",index=False
    )

if __name__ == '__main__':
    append_recent_streams()
    download_recent_top("short")
    download_recent_top("medium")
    download_recent_top("long")
    
    
    