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


def create_spot_df(api_return):
    """
    iterator that returns a dictionary of the relevant information from the html repsonse

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


def create_spot_df_top(api_return):
    """
    iterator that returns a dictionary of the relevant information from the html repsonse

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


def download_tracks():
    url = "me/tracks"
    with requests_cache.CachedSession("spotify_cache") as s:

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # hit the endpoint once to get the first 'next' url
        r = s.get(PREFIX + url, headers=headers)
        df = pd.DataFrame(create_spot_df(r.json()))

        while r.status_code == 200:
            next_url = r.json()["next"]
            if next_url is None:
                break
            logger.debug(f"Requesting data from {next_url}")
            r = s.get(next_url, headers=headers)
            logger.debug(f"Request Status:{r.status_code}")
            df2 = pd.DataFrame(create_spot_df(r.json()))
            df = pd.concat([df, df2], ignore_index=True)

        df.to_csv("./data_out/all_tracks.csv")


def download_recent_top(time_range):
    url = f"me/top/tracks?time_range={time_range}_term"
    with requests_cache.CachedSession("spotify_cache") as s:

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # hit the endpoint once to get the first 'next' url
        logger.debug(f"Requesting data from {PREFIX+url}")
        r = s.get(PREFIX + url, headers=headers)
        df = pd.DataFrame(create_spot_df_top(r.json()))

        while r.status_code == 200:
            next_url = r.json()["next"]
            if next_url is None:
                break
            logger.debug(f"Requesting data from {next_url}")
            r = s.get(next_url, headers=headers)
            logger.debug(f"Request Status: {r.status_code}")
            df2 = pd.DataFrame(create_spot_df_top(r.json()))
            df = pd.concat([df, df2], ignore_index=True)

        df.to_csv(f"./data_out/top_tracks_{time_range}.csv")


if __name__ == "__main__":

    download_tracks()

    download_recent_top("short")
    download_recent_top("medium")
    download_recent_top("long")

# %%
