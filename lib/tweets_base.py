import os
import logging
import json

from .shared import tweets_folder, data_folder, tweetsFetchSettings
from .twitter_auth import get_api_app

def readTweetFromFolder(id, folder = tweetsFetchSettings['folder']):
    ff = os.path.join(tweets_folder, folder)
    with open(os.path.join(ff, '{}.json'.format(id)), 'r') as f:
        return json.load(f)

def writeTweetToFolder(tweet, folder = tweetsFetchSettings['folder']):
    ff = os.path.join(tweets_folder, folder)
    with open(os.path.join(ff, '{}.json'.format(tweet['id_str'])), 'w') as f:
        json.dump(tweet, f)

def deleteTweetFromFolder(id, folder = tweetsFetchSettings['folder']):
    ff = os.path.join(tweets_folder, folder)
    os.remove(os.path.join(ff, '{}.json'.format(id)))

def readTweetsFromFolder(folder = tweetsFetchSettings['folder']):
    ff = os.path.join(tweets_folder, folder)
    tweets = [readTweetFromFolder(f[:-5], folder) for f in os.listdir(ff) if f[-5:] == '.json']
    logging.info('Read {} tweets from folder: \'{}\''.format(len(tweets), folder))
    return tweets


def readTweetFromTwitter(id):
    api = get_api_app()
    logging.info('Reading tweet info from twitter API: {}'.format(id))
    return api.get_status(id, include_entities=True, tweet_mode='extended')._json


def writeTweetsApiJson(data, tweetsApiFile = tweetsFetchSettings['file']):
    filePath = os.path.join(data_folder, tweetsApiFile)
    logging.info('Writing new tweets API file: \'{}\''.format(tweetsApiFile))
    with open(filePath, 'w') as f:
        json.dump(data, f)

def readTweetsApiJson(tweetsApiFile = tweetsFetchSettings['file']):
    with open(os.path.join(data_folder, tweetsApiFile), 'r') as f:
        return json.load(f)
