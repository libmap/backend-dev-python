from tweepy import AppAuthHandler, OAuthHandler, API
from .shared import base_folder, twitterAuth
import json
import os


def get_auth_app():
    ad = twitterAuth['api']
    return AppAuthHandler(ad['key'], ad['secret'])

def get_api_app():
    return API(get_auth_app())

def get_auth_user():
    ad = twitterAuth
    auth = OAuthHandler(ad['api']['key'], ad['api']['secret'])
    auth.set_access_token(ad['access']['token'], ad['access']['token-secret'])
    return auth
