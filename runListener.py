#!./venv/bin/python
import json
import tweepy
import os
import logging

from lib.twitterAuth import get_auth_user
from lib.tweets_aux import createAndwriteTweetsApiJson
from lib.shared import data_folder, tweets_folder, base_folder, tweetsFetchSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(base_folder, 'log/listener.log')),
        logging.StreamHandler()
    ]
)

searchString = tweetsFetchSettings['listen']
tweets_search_folder = os.path.join(tweets_folder, tweetsFetchSettings['folder'])

class DecarbnowStreamListener(tweepy.StreamListener):
    def on_status(self, tweet):
        id = tweet._json['id']
        logging.info('Listener got new tweet: {}'.format(id))
        with open(os.path.join(tweets_search_folder, '{}.json').format(id), 'w') as json_file:
            json.dump(tweet._json, json_file)

        createAndwriteTweetsApiJson(tweetsFetchSettings['folder'], tweetsFetchSettings['file'])

    def on_error(self, status_code):
        logging.warning('Listener got error, status code: {}'.format(status_code))
        return True


logging.info('Init Listener:')
logging.info('  - Tweets Folder: \'{}\''.format(tweetsFetchSettings['folder']))
logging.info('  - Search String: \'{}\''.format(searchString))

listener = DecarbnowStreamListener()
stream = tweepy.Stream(auth = get_auth_user(), listener = listener, tweet_mode = 'extended')

logging.info('Init Tweets API File ...')
createAndwriteTweetsApiJson(tweetsFetchSettings['folder'], tweetsFetchSettings['file'])

logging.info('Start Listener ...')
try:
    stream.filter(track=[searchString])
except KeyboardInterrupt:
    pass
