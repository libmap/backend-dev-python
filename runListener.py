##!./venv/bin/python

import os
import logging
import time
from mastodon import StreamListener

from lib.shared import base_folder, tootsFetchSettings, toots_folder
from lib.mastodon_auth import get_auth_user
from lib.mastodon_base import writeTootToFolder, writeTootToArchive, readTootFromFolder, deleteTootFromFolder
from lib.TootForest import TootForest


mastodon = get_auth_user()

keyword = tootsFetchSettings['listen']

dir_path = os.path.join(toots_folder, tootsFetchSettings['folder'])
files = os.listdir(dir_path)
existing_ids = [os.path.splitext(file)[0] for file in files]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(base_folder, 'log/listener.log')),
        logging.StreamHandler()
    ]
)

searchString = tootsFetchSettings['listen']

def update():
    global existing_ids
    forest = TootForest.fromFolder(tootsFetchSettings['folder'])
    forest.saveApiJson(tootsFetchSettings['file'])
    
    # Update the global existing_ids variable
    files = os.listdir(dir_path)
    existing_ids = [os.path.splitext(file)[0] for file in files]


class MastodonStreamListener(StreamListener):
    def __init__(self, mastodon):
        self.mastodon = mastodon
        self.receivedHeartbeat = False

    def stream_with_reconnection(self):
        retry_delay = 10
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.mastodon.stream_public(self)
                retry_count = 0
                break
            except Exception as e:
                self.receivedHeartbeat = False
                logging.warning("Error: ", e)
                logging.info("Trying to reconnect after " + str(retry_delay) + " seconds.")
                retry_count += 1
                time.sleep(retry_delay)

    def on_update(self, toot):     
        if keyword in toot['content']:
            id = str(toot['id'])  # Convert the ID to a string, if it's not already
            logging.info('Listener got new toot: {}'.format(id))
            writeTootToFolder(toot, tootsFetchSettings['folder'])
            update()

    def on_status_update(self, toot):     
        if keyword in toot['content']:
            id = toot['id']
            logging.info('Listener got update of toot: {}'.format(id))
            writeTootToFolder(toot, tootsFetchSettings['folder'])
            update()

    def on_delete(self, status_id):
        str_status = str(status_id)
        if str_status in existing_ids:
            logging.info('Archiving toot (id: {})!'.format(str_status))
            toot = readTootFromFolder(str_status)
            archive_dir = os.path.join(toots_folder, tootsFetchSettings['folder'], 'archive')
            os.makedirs(archive_dir, exist_ok=True)

            writeTootToArchive(toot, tootsFetchSettings['folder'])
            deleteTootFromFolder(status_id, tootsFetchSettings['folder'])
            update()

    def handle_heartbeat(self):
        if not self.receivedHeartbeat:
            logging.info("Connected to server. Listening.")
            self.receivedHeartbeat = True

    def on_abort(self, status_code):
        logging.warning('Listener got error, status code: {}'.format(status_code))
        self.stream_with_reconnection()

logging.info('Init Listener:')
logging.info('  - Toots Folder: \'{}\''.format(tootsFetchSettings['folder']))
logging.info('  - Search String: \'{}\''.format(searchString))

listener = MastodonStreamListener(mastodon)

logging.info('Init Toots API File ...')
update()

logging.info('Start Listener ...')
listener.stream_with_reconnection()