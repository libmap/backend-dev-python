import json
import os
import logging
import GetOldTweets3 as got

from .shared import tweets_folder, tweetsFetchSettings
from .tweets_base import *

def getOldTweetIds(searchString = tweetsFetchSettings['link'], max = 100):
    tweetCriteria = got.manager.TweetCriteria().setQuerySearch(searchString)\
                                               .setMaxTweets(max)
    logging.info('Loading old tweet ids from twitter (GoT):')
    logging.info('  - Search String: \'{}\''.format(searchString))
    logging.info('  - Max Tweets: {}'.format(max))

    tweets = got.manager.TweetManager.getTweets(tweetCriteria)

    logging.info('Got {} tweets:'.format(len(tweets)))
    for t in tweets:
        logging.info('  - {}: \'{}\''.format(t.id, t.text))

    return [t.id for t in tweets]

def populateTweetsFolder(folder = tweetsFetchSettings['folder'], ids = [], init = False, refresh = False):
    d = os.path.join(tweets_folder, folder)
    if not os.path.exists(d):
        os.mkdir(d)
    ids_e = [f[:-5] for f in os.listdir(d)]
    if init:
        for fp in os.listdir(d):
            os.remove(os.path.join(folder, fp))
        ids_e = []

    if refresh:
        ids_f = ids
    else:
        ids_f = list(set(ids) - set(ids_e))

    for id in ids_f:
        info = readTweetFromTwitter(id)
        writeTweetToFolder(info, folder)
