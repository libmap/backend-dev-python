#!/usr/bin/env python
import sys
import json
import tweepy

from lib.twitter import get_auth_user

class DecarbnowStreamListener(tweepy.StreamListener):
    def on_status(self, tweet):
        print(tweet._json['id'])
        with open('data/tmp/{}.json'.format(tweet._json['id']), 'w') as json_file:
            json.dump(tweet._json, json_file)

    def on_error(self, status_code):
        print('Error occured, status code: ' + str(status_code))
        return True

listener = DecarbnowStreamListener()
stream = tweepy.Stream(auth = get_auth_user(), listener = listener, tweet_mode = 'extended')

#stream.filter(track=['corona'], is_async=True)
#stream.filter(track=['map.decarbnow.abteil.org'])
stream.filter(track=['decarbnow_test'])
