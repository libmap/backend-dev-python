import os
import json

lib_folder = os.path.dirname(os.path.realpath(__file__))

base_folder = os.path.join(lib_folder, '..')
data_folder = os.path.join(base_folder, 'data')
tweets_folder = os.path.join(data_folder, 'tweets')

with open(os.path.join(base_folder, 'config.json'), 'r') as f:
    config = json.load(f)

tweetsFetchSettings = config['tweetsFetchSettings']['list'][config['tweetsFetchSettings']['default']]
authToken = config['authToken']
