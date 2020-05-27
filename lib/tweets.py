from .shared import data_folder
import json
import os

def readTweetsFromFolder(folder = 'tweets'):
    folder = os.path.join(data_folder, folder)
    tweets = []
    for fp in os.listdir(folder):
        with open(os.path.join(folder, fp), 'r') as f:
            tweets.append(json.load(f))
    return tweets

def getPathsOfLinks(tweet, to = 'map.decarbnow.abteil.org'):
    if not tweet['entities']['urls']:
        return []
    ul = [u['expanded_url'] for u in tweet['entities']['urls']]
    return [u.split(to, 1)[1] for u in ul if to in u]

def tweetToApiFormat(tweet, add = {}):
    hashtags = []
    if tweet['entities']['hashtags']:
        hashtags = [h['text'] for h in tweet['entities']['hashtags']]
    paths = getPathsOfLinks(tweet)
    return {
        'url': paths[0],
        'hashtags': hashtags,
        **add
    }

class TweetTree:
    def __init__(self, tweets):
        tweetsDict = {t['id_str']: t for t in tweets}

        tree = []
        for tweet in tweetsDict.values():
            if     tweet['in_reply_to_status_id_str'] \
               and tweet['in_reply_to_status_id_str'] in tweetsDict \
               and tweet['in_reply_to_user_id_str'] == tweet['user']['id_str']:
                p = tweetsDict[tweet['in_reply_to_status_id_str']]
                if not '_children' in p:
                    p['_children'] = []
                p['_children'].append(tweet)
            else:
                tree.append(tweet)

        self.tree = tree

    def __str__(self):
        def printLeafs(tweets, i = 0):
            a = []
            for tweet in tweets:
                a.append("{} - {} ({})".format('  ' * i, tweet['id_str'], tweet['created_at']))
                if '_children' in tweet:
                    a.extend(printLeafs(tweet['_children'], i + 1))
            return a
        return '\n'.join(printLeafs(self.tree))

    def getApiJson(self):
        apiJson = {};
        for tweet in self.tree:
            tweetId = tweet['id_str']
            if '_children' in tweet and len(tweet['_children']) > 0:
                story = tweetId
                apiJson[tweetId] = tweetToApiFormat(tweet, {'story': story})
                while '_children' in tweet and len(tweet['_children']) > 0:
                    # ONLY FIRST CHILD
                    tweet = tweet['_children'][0]
                    tweetId = tweet['id_str']
                    apiJson[tweetId] = tweetToApiFormat(tweet, {'story': story})
            else:
                apiJson[tweetId] = tweetToApiFormat(tweet)

        return apiJson
