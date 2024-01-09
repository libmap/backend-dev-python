from mastodon import Mastodon
from .shared import base_folder, mastodonAuth
import json
import os

with open(os.path.join(base_folder, 'config.json'), 'r') as f:
    config = json.load(f)

def get_auth_user():
    return Mastodon(
        client_id = config['mastodon']['client']['key'],
        client_secret = config['mastodon']['client']['secret'],
        access_token = config['mastodon']['access']['token'],
        api_base_url = config['mastodon']['instance_url']
    )
