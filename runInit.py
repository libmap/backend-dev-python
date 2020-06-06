#!/usr/bin/env python
import json
import os
import logging
import GetOldTweets3 as got

from lib.shared import base_folder, tweetsFetchSettings
from lib.tweets import getOldTweetIds, populateTweetsFolder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(base_folder, 'log/init.log')),
        logging.StreamHandler()
    ]
)

# searchString = 'map.decarbnow.abteil.org'
searchString = tweetsFetchSettings['init']
folder = tweetsFetchSettings['folder']

ids = getOldTweetIds(searchString)
populateTweetsFolder(folder, ids)
