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
        # Determine source platform
        source = 'mastodon.social'  # Default
        if 'platform' in self.data:
            if self.data['platform'] == 'bluesky':
                source = 'bluesky'

        return {
            'url': self.getPathOfLinksTo()[0],
            'hashtags': self.getHashtags(),
            'timestamp': str(self.getDateTime()),
            'content': self.getText(),
            'account': self.getUserName(),
            'display_name': self.getUserScreenName(),
            'avatar': self.getUserImageHttps(),
            'media': self.getMedia(),
            'source': source,
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
        return self.data['account'].get('id', self.data['account'].get('acct', ''))

    def getUserName(self):
        return self.data['account']['username']

    def getUserScreenName(self):
        return self.data['account']['display_name']
    
    def getUserImageHttps(self):
        return self.data['account'].get('avatar_static', '')

    def getDateTime(self):
        date_str = self.data['created_at']
        # Handle different date formats (Mastodon vs Bluesky)
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # ISO format with microseconds (Bluesky)
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                # Fallback - return current time if parsing fails
                return datetime.now()

    def getMedia(self):
        media = []
        # Handle Mastodon-style media
        if 'media_attachments' in self.data:
            media.extend([item['preview_url'] for item in self.data['media_attachments'] if 'preview_url' in item])
        # Handle Bluesky media from embed
        if 'platform' in self.data and self.data['platform'] == 'bluesky' and 'raw_record' in self.data:
            raw_record = self.data['raw_record']
            if 'embed' in raw_record:
                # Handle image embeds
                if raw_record['embed'].get('$type') == 'app.bsky.embed.images' and 'images' in raw_record['embed']:
                    for image in raw_record['embed']['images']:
                        if 'image' in image and '$link' in image['image']['ref']:
                            # Convert blob reference to CDN URL
                            blob_ref = image['image']['ref']['$link']
                            cdn_url = f"https://cdn.bsky.app/img/feed_thumbnail/plain/did:plc:adsquh2z4vzbpeelyvkq4rbl/{blob_ref}@jpeg"
                            media.append(cdn_url)
        return media

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
        # Handle Mastodon-style tags
        if 'tags' in self.data and self.data['tags']:
            hashtags.extend([h['name'] for h in self.data['tags']])
        # Handle extended_toot format
        if 'extended_toot' in self.data and 'entities' in self.data['extended_toot'] and 'hashtags' in self.data['extended_toot']['entities']:
            hashtags.extend([h['text'] for h in self.data['extended_toot']['entities']['hashtags']])
        # Handle Bluesky hashtags from facets
        if 'platform' in self.data and self.data['platform'] == 'bluesky' and 'raw_record' in self.data:
            raw_record = self.data['raw_record']
            if 'facets' in raw_record:
                for facet in raw_record['facets']:
                    if 'features' in facet:
                        for feature in facet['features']:
                            if feature.get('$type') == 'app.bsky.richtext.facet#tag' and 'tag' in feature:
                                hashtags.append(feature['tag'])
        return hashtags

    def hasHashtag(self, hashtag):
        return hashtag in self.getHashtags()

    def getLinks(self):
        urls = []
        content = self.getText()

        # For Bluesky posts - extract URLs from structured data first
        if 'platform' in self.data and self.data['platform'] == 'bluesky' and 'raw_record' in self.data:
            raw_record = self.data['raw_record']

            # Extract from embed.external.uri
            if 'embed' in raw_record and 'external' in raw_record['embed'] and 'uri' in raw_record['embed']['external']:
                urls.append(raw_record['embed']['external']['uri'])

            # Extract from facets (rich text links)
            if 'facets' in raw_record:
                for facet in raw_record['facets']:
                    if 'features' in facet:
                        for feature in facet['features']:
                            if feature.get('$type') == 'app.bsky.richtext.facet#link' and 'uri' in feature:
                                urls.append(feature['uri'])

        # For Mastodon posts with HTML content
        if 'content' in self.data and '<' in self.data['content']:
            extractor = URLExtractor()
            extractor.feed(self.data['content'])
            urls.extend(extractor.urls)

        # Fallback: extract URLs from plain text content using regex
        if content:
            import re
            # Match URLs in plain text (http/https URLs)
            url_pattern = r'https?://[^\s<>"]+|[a-zA-Z0-9][-a-zA-Z0-9]*\.(?:[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)[^\s<>"]*'
            text_urls = re.findall(url_pattern, content)
            urls.extend(text_urls)

        return list(set(urls))  # Remove duplicates

    def getPathOfLinksTo(self, to = tootsFetchSettings['link']):
        links = self.getLinks()
        matching_links = [u for u in links if to in u]

        # For Bluesky posts, prioritize full URLs (those starting with https://) over truncated ones
        if 'platform' in self.data and self.data['platform'] == 'bluesky':
            # Sort so full URLs come first
            matching_links.sort(key=lambda x: not x.startswith('https://'))

        return [u.split(to, 1)[1] for u in matching_links]

    def hasLinkTo(self, to = f"{tootsFetchSettings['link']}/@"):
        return len(self.getPathOfLinksTo(to)) > 0

    def getUrl(self):
        if 'url' in self.data:
            return self.data['url']
