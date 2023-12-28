from .shared import tweets_folder, tweetsFetchSettings
from .twitter_auth import get_api_app
from .tweets_base import *

from datetime import datetime

class Tweet(object):
    data = None

    @staticmethod
    def loadFromFile(id, folder = tweetsFetchSettings['folder']):
        return Tweet(readTweetFromFolder(id, folder))

    @staticmethod
    def loadFromFolder(folder = tweetsFetchSettings['folder']):
        return [Tweet(j) for j in readTweetsFromFolder(folder)]

    @staticmethod
    def loadFromTwitter(id):
        return Tweet(readTweetFromTwitter(id))


    def __init__(self, data):
        self.data = data
        self.children = []

    def save(self, folder = tweetsFetchSettings['folder']):
        writeTweetToFolder(self.data, folder)

    def delete(self, folder = tweetsFetchSettings['folder']):
        deleteTweetFromFolder(self.getId(), folder)

    def addChild(self, tweet):
        self.children.append(tweet)

    def getChildren(self):
        return self.children

    def hasChildren(self):
        return len(self.children) > 0

    def asApiDict(self, add = {}):
        return {
            'url': self.getPathOfLinksTo()[0],
            'hashtags': self.getHashtags(),
            'timestamp': str(self.getDateTime()),
            'content': self.getText(),
            'account': self.getUserName(),
            'display_name': self.getUserScreenName(),
            'avatar': self.getUserImageHttps(),
            **add
        }

    def getData(self):
        return self.data

    def toStringList(self):
        return [
            "{}, {}, {}".format(self.getUserName(), self.getDateTime(), self.getId()),
            "# {}".format(', '.join(self.getHashtags())),
            "▶ {}".format(', '.join(self.getLinks())),
            "¶ {}".format(self.getText())
        ]

    def __str__(self):
        return '\n'.join(self.toStringList())

    def getId(self):
        return self.data['id_str']

    def getUserId(self):
        return self.data['user']['id_str']

    def getUserName(self):
        return self.data['user']['name']

    def getUserScreenName(self):
        return self.data['user']['screen_name']
    
    def getUserImageHttps(self):
        return self.data['user']['profile_image_url_https']

    def getDateTime(self):
        return datetime.strptime(self.data['created_at'], '%a %b %d %H:%M:%S +0000 %Y')

    def getText(self):
        if 'full_text' in self.data:
            return self.data['full_text']
        elif 'extended_tweet' in self.data:
            if 'full_text' in self.data['extended_tweet']:
                return self.data['extended_tweet']['full_text']
        elif 'text' in self.data:
            return self.data['text']

    def isReply(self):
        return 'in_reply_to_status_id_str' in self.data

    def getReplyToId(self):
        return self.data['in_reply_to_status_id_str']

    def getReplyToUserId(self):
        return self.data['in_reply_to_user_id_str']

    def isSelfReply(self):
        return self.isReply() and self.getUserId() == self.getReplyToUserId()

    def getHashtags(self):
        hashtags = []
        if self.data['entities']['hashtags']:
            hashtags.extend([h['text'] for h in self.data['entities']['hashtags']])
        if 'extended_tweet' in self.data and self.data['extended_tweet']['entities']['hashtags']:
            hashtags.extend([h['text'] for h in self.data['extended_tweet']['entities']['hashtags']])
        return hashtags

    def hasHashtag(self, hashtag):
        return hashtag in self.getHashtags()

    def getLinks(self):
        urls = []
        if self.data['entities']['urls']:
            urls.extend([url['expanded_url'] for url in self.data['entities']['urls']])
        if 'extended_tweet' in self.data and self.data['extended_tweet']['entities']['urls']:
            urls.extend([url['expanded_url'] for url in self.data['extended_tweet']['entities']['urls']])
        return urls

    def getPathOfLinksTo(self, to = tweetsFetchSettings['link']):
        return [u.split(to, 1)[1] for u in self.getLinks() if to in u]

    def hasLinkTo(self, to = tweetsFetchSettings['link']):
        return len(self.getPathOfLinksTo(to)) > 0

    def getUrl(self):
        return 'https://twitter.com/{}/status/{}'.format(self.getUserScreenName(), self.getId())
