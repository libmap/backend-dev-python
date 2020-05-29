#!/usr/bin/env python
import json
import tweepy
import copy
import os
from lib.tweets import *
from lib.shared import data_folder, tweets_folder

searchString = 'map.decarbnow.abteil.org'
tweets_search_folder = os.path.join(tweets_folder, searchString)

def createAndwriteApiJson():
    tweets = readTweetsFromFolder(searchString)
    print('Count tweets {}'.format(len(tweets)))
    tweetsFilter = [t for t in tweets if len(getPathsOfLinks(t)) > 0]
    print('Count filtered tweets {}'.format(len(tweetsFilter)))
    tree = TweetTree(tweets)
    print(tree)
    apiJson = tree.getApiJson()
    with open(os.path.join(data_folder, 'api.json'), 'w') as json_file:
        json.dump(apiJson, json_file)
        print('New JSON Api file written.')


from lib.twitterAuth import get_auth_user

class DecarbnowStreamListener(tweepy.StreamListener):
    def on_status(self, tweet):
        id = tweet._json['id']
        print('Getting new tweet with id: {}'.format(id))
        with open(os.path.join(tweets_search_folder, '{}.json').format(id), 'w') as json_file:
            json.dump(tweet._json, json_file)
        createAndwriteApiJson()

    def on_error(self, status_code):
        print('Error occured, status code: ' + str(status_code))
        return True

listener = DecarbnowStreamListener()
stream = tweepy.Stream(auth = get_auth_user(), listener = listener, tweet_mode = 'extended')

#stream.filter(track=['corona'], is_async=True)
#stream.filter(track=['map.decarbnow.abteil.org'])

createAndwriteApiJson()
stream.filter(track=[searchString])
