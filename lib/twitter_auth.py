from tweepy import AppAuthHandler, OAuthHandler, API
from .shared import base_folder
import json
import os

def read_auth_json():
    ad = None
    with open(os.path.join(base_folder, 'twitter-auth.json')) as json_file:
        ad = json.load(json_file)
    if ad is None:
        raise Exception('Auth missing')
    return ad

def get_auth_app():
    ad = read_auth_json()['api']
    return AppAuthHandler(ad['key'], ad['secret'])

def get_api_app():
    return API(get_auth_app())

def get_auth_user():
    ad = read_auth_json()
    auth = OAuthHandler(ad['api']['key'], ad['api']['secret'])
    auth.set_access_token(ad['access']['token'], ad['access']['token-secret'])
    return auth
