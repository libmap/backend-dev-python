from .shared import toots_folder, tootsFetchSettings
#from .mastodon_auth import get_api_app
from .mastodon_base import *

from datetime import datetime
from html.parser import HTMLParser

class URLExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.extend(value for name, value in attrs if name == 'href')

class Toot(object):
    data = None

    @staticmethod
    def loadFromFile(id, folder = tootsFetchSettings['folder']):
        return Toot(readTootFromFolder(id, folder))

    @staticmethod
    def loadFromFolder(folder = tootsFetchSettings['folder']):
        return [Toot(j) for j in readTootsFromFolder(folder)]

    @staticmethod
    def loadFromMastodon(id):
        return Toot(readTootFromMastodon(id))


    def __init__(self, data):
        self.data = data
        self.children = []

    def save(self, folder = tootsFetchSettings['folder']):
        writeTootToFolder(self.data, folder)

    def delete(self, folder = tootsFetchSettings['folder']):
        deleteTootFromFolder(self.getId(), folder)

    def addChild(self, toot):
        self.children.append(toot)

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
            'media': self.getMedia(),
            'source': 'mastodon.social',
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
        return self.data['id']

    def getUserId(self):
        return self.data['account']['id']

    def getUserName(self):
        return self.data['account']['username']

    def getUserScreenName(self):
        return self.data['account']['display_name']
    
    def getUserImageHttps(self):
        return self.data['account']['avatar_static']

    def getDateTime(self):
        return datetime.strptime(self.data['created_at'], '%Y-%m-%d %H:%M:%S')

    def getMedia(self):
        if 'media_attachments' in self.data:
            return [item['preview_url'] for item in self.data['media_attachments'] if 'preview_url' in item]
        return []

    def getText(self):
        if 'content' in self.data:
            return self.data['content']
        elif 'extended_toot' in self.data:
            if 'full_text' in self.data['extended_toot']:
                return self.data['extended_toot']['full_text']
        elif 'retooted_status' in self.data and 'extended_toot' in self.data['retooted_status'] and self.data['retooted_status']['extended_toot']['full_text']:
            return self.data['retooted_status']['extended_toot']['full_text']
        elif 'text' in self.data:
            return self.data['text']

    def isReply(self):
        return 'in_reply_to_id' in self.data

    def getReplyToId(self):
        return self.data['in_reply_to_id']

    def getReplyToUserId(self):
        return self.data['in_reply_to_account_id']

    def isSelfReply(self):
        return self.isReply() and self.getUserId() == self.getReplyToUserId()

    def getHashtags(self):
        hashtags = []
        if self.data['tags']:
            hashtags.extend([h['name'] for h in self.data['tags']])
        if 'extended_toot' in self.data and self.data['extended_toot']['entities']['hashtags']:
            hashtags.extend([h['text'] for h in self.data['extended_toot']['entities']['hashtags']])
        return hashtags

    def hasHashtag(self, hashtag):
        return hashtag in self.getHashtags()

    def getLinks(self):
        urls = []
        if 'content' in self.data:
            extractor = URLExtractor()
            extractor.feed(self.data['content'])
            urls.extend(extractor.urls)
        return urls

    def getPathOfLinksTo(self, to = tootsFetchSettings['link']):
        return [u.split(to, 1)[1] for u in self.getLinks() if to in u]

    def hasLinkTo(self, to = f"{tootsFetchSettings['link']}/@"):
        return len(self.getPathOfLinksTo(to)) > 0

    def getUrl(self):
        if 'url' in self.data:
            return self.data['url']
