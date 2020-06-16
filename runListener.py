#!./venv/bin/python
import json
import tweepy
import os
import logging

from lib.shared import base_folder, tweetsFetchSettings
from lib.twitter_auth import get_auth_user
from lib.tweets_base import writeTweetToFolder
from lib.TweetForest import TweetForest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(base_folder, 'log/listener.log')),
        logging.StreamHandler()
    ]
)

searchString = tweetsFetchSettings['listen']

def update():
    forest = TweetForest.fromFolder(tweetsFetchSettings['folder'])
    forest.saveApiJson(tweetsFetchSettings['file'])

class DecarbnowStreamListener(tweepy.StreamListener):
    def on_status(self, tweet):
        id = tweet._json['id']
        logging.info('Listener got new tweet: {}'.format(id))
        writeTweetToFolder(tweet._json, tweetsFetchSettings['folder'])
        update()

    def on_error(self, status_code):
        logging.warning('Listener got error, status code: {}'.format(status_code))
        return True


logging.info('Init Listener:')
logging.info('  - Tweets Folder: \'{}\''.format(tweetsFetchSettings['folder']))
logging.info('  - Search String: \'{}\''.format(searchString))

listener = DecarbnowStreamListener()
stream = tweepy.Stream(auth = get_auth_user(), listener = listener, tweet_mode = 'extended')

logging.info('Init Tweets API File ...')
update()

logging.info('Start Listener ...')
try:
    stream.filter(track=[searchString])
except KeyboardInterrupt:
    pass
