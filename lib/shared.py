import os
import json

lib_folder = os.path.dirname(os.path.realpath(__file__))

base_folder = os.path.join(lib_folder, '..')
data_folder = os.path.join(base_folder, 'data')
toots_folder = os.path.join(data_folder, 'toots')

with open(os.path.join(base_folder, 'config.json'), 'r', encoding='utf-8') as f:
    config = json.load(f)

tootsFetchSettings = config['tootsFetchSettings']['list'][config['tootsFetchSettings']['default']]

authToken = config['authToken']
secretKey = config['secretKey']
mastodonAuth = config['mastodon']
