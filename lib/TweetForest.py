from .shared import tweetsFetchSettings
from .tweets_base import readTweetsFromFolder, writeTweetsApiJson
from .Tweet import Tweet

class TweetForest(object):
    trunks = []

    @staticmethod
    def fromFolder(folder = tweetsFetchSettings['folder']):
        tweets = [Tweet(j) for j in readTweetsFromFolder(folder)]
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

    def saveApiJson(self, file = tweetsFetchSettings['file']):
        writeTweetsApiJson(self.asApiJson(), file)
