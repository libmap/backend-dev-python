#!/usr/bin/env python
import tweepy
import sys

sys.path.append("..")
from lib.helpers import get_auth_user

class DecarbnowStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print(status.text)
    def on_error(self, status_code):
        print('Error occured, status code: ' + str(status_code))
        return True

listener = DecarbnowStreamListener()
stream = tweepy.Stream(auth = get_auth_user(), listener=listener)

#stream.filter(track=['corona'], is_async=True)
stream.filter(track=['vienna', 'wien'])
