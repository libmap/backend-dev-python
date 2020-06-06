import json
import os
import logging
import GetOldTweets3 as got

from .shared import tweets_folder, data_folder
from .TweetTree import TweetTree, readTweetsFromFolder, getPathsOfLinks
from .twitterAuth import get_api_app

def getOldTweetIds(searchString, max = 100):
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

def createAndwriteTweetsApiJson(folder, tweetsApiFile = 'tweetsApi.json'):
    tweets = readTweetsFromFolder(folder)
    tweetsFilter = [t for t in tweets if len(getPathsOfLinks(t)) > 0]
    tree = TweetTree(tweetsFilter)
    filePath = os.path.join(data_folder, tweetsApiFile)
    logging.info('Writing new tweets API file: \'{}\''.format(tweetsApiFile))
    with open(filePath, 'w') as json_file:
        json.dump(tree.getApiJson(), json_file)

def readTweetsApiJson(tweetsApiFile = 'tweetsApi.json'):
    with open(os.path.join(data_folder, tweetsApiFile), 'r') as f:
        return json.load(f)

def readTweetIdsFromTwitter(ids):
    api = get_api_app()
    tweets = {}
    for id in ids:
        logging.info('Reading tweet info from twitter API: {}'.format(id))
        tweets[id] = api.get_status(id, include_entities=True, tweet_mode='extended')._json
    return tweets

def populateTweetsFolder(folder, ids_n, init = False, refresh = False):
    d = os.path.join(tweets_folder, folder)
    if not os.path.exists(d):
        os.mkdir(d)
    ids_e = [f[:-5] for f in os.listdir(d)]
    if init:
        for fp in os.listdir(d):
            os.remove(os.path.join(folder, fp))
        ids_e = []

    if refresh:
        ids = ids_n
    else:
        ids = list(set(ids_n) - set(ids_e))

    tweets = readTweetIdsFromTwitter(ids)
    for id, info in tweets.items():
        with open(os.path.join(d, '{}.json'.format(id)), 'w') as json_file:
            json.dump(info, json_file)
