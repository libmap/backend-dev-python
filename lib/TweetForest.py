from .shared import tweetsFetchSettings
from .tweets_base import readTweetsFromFolder, writeTweetsApiJson
from .Tweet import Tweet
from collections import OrderedDict

class TweetForest(object):
    trunks = []

    @staticmethod
    def fromFolder(folder = tweetsFetchSettings['folder']):
        tweets = Tweet.loadFromFolder(folder)
        tweets = filter(lambda t: t.hasLinkTo(), tweets)
        # tweets = filter(lambda t: not t.hasHashtag('private'), tweets)
        return TweetForest(tweets)

    def __init__(self, tweets):
        self.trunks = []
        tweetsDict = {t.getId(): t for t in tweets}

        for tweet in tweetsDict.values():
            if tweet.isSelfReply():
                if tweet.getReplyToId() in tweetsDict:
                    tweetsDict[tweet.getReplyToId()].addChild(tweet)
                    continue

            self.trunks.append(tweet)

    def __str__(self):
        def printLeafs(tweets, i = 0):
            a = []
            for tweet in tweets:
                a.extend(["{}{}".format('  ' * i, l) for l in tweet.toStringList()])
                a.append('')
                if tweet.hasChildren():
                    a.extend(printLeafs(tweet.getChildren(), i + 1))
            return a
        return '\n'.join(printLeafs(self.trunks))

    def asApiJson(self):
        apiJson = {};
        for tweet in self.trunks:
            if tweet.hasChildren():
                story = tweet.getId()
                apiJson[story] = tweet.asApiDict({'story': story})
                while tweet.hasChildren():
                    # ONLY FIRST CHILD
                    tweet = tweet.getChildren()[0]
                    apiJson[tweet.getId()] = tweet.asApiDict({'story': story})
            else:
                apiJson[tweet.getId()] = tweet.asApiDict()

        return apiJson
    
    def rename_ids(self, data):
        # Create a dictionary to store the count of each story ID
        story_counts = {}

        # Create a dictionary to store the length of each story
        story_lengths = {}

        # Calculate the length of each story before the loop
        for tweet_id, values in data.items():
            # Check if "story" key is present, otherwise use tweet_id as the story ID
            story_id = values.get("story", tweet_id)

            # Update the length of the story
            story_lengths[story_id] = story_lengths.get(story_id, 0) + 1

        # Iterate through the original dictionary and create a new one with modified keys
        result = {}
        for tweet_id, values in data.items():
            # Check if "story" key is present, otherwise use tweet_id as the story ID
            story_id = values.get("story", tweet_id)

            # Calculate the count as the difference between the length of the story and the current length
            count = story_lengths[story_id]
            story_lengths[story_id] = story_lengths[story_id] - 1

            # Create the new key in the format "story_id.count_tweet_id"
            new_key = f"{story_id}.{count}_{tweet_id}"
            result[new_key] = values

        return result
    
    def revert_ids(self, data):
        # Iterate through the dictionary and create a new one with reverted keys
        result = {}
        for key, values in data.items():
            # Split the key into story_id.count_tweet_id
            parts = key.split('_')

            # Extract the tweet_id from the second part
            tweet_id = parts[1]

            # Create the new key with the original tweet_id
            new_key = tweet_id
            result[new_key] = values

        return result

    def saveApiJson(self, file = tweetsFetchSettings['file']):
        data = self.asApiJson()
        renamed_data = self.rename_ids(data)
        # Sort tweets based on id in descending order
        sorted_tweets = OrderedDict(sorted(renamed_data.items(), key=lambda x: x[0], reverse=True))
        final_tweets = self.revert_ids(sorted_tweets)

        writeTweetsApiJson(final_tweets, file)
