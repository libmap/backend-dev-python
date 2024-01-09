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
# Get all files in directory
files = os.listdir(dir_path)
# Extract ids (filenames without .json)
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
    forest = TootForest.fromFolder(tootsFetchSettings['folder'])
    forest.saveApiJson(tootsFetchSettings['file'])

class DecarbnowStreamListener(StreamListener):
    def __init__(self, mastodon):
        self.mastodon = mastodon
        self.receivedHeartbeat = False

    def stream_with_reconnection(self):
        retry_delay = 5
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.mastodon.stream_public(self)
                break
            except Exception as e:
                self.receivedHeartbeat = False
                print("Error: ", e)
                print("Versuche, die Verbindung nach 10 Sekunden erneut herzustellen...")
                retry_count += 1
                time.sleep(retry_delay)

    def on_update(self, toot):     
        if keyword in toot['content']:
            id = toot['id']
            logging.info('Listener got new toot: {}'.format(id))
            writeTootToFolder(toot, tootsFetchSettings['folder'])
            update()

    def on_status_update(self, toot):     
        if keyword in toot['content']:
            id = toot['id']
            logging.info('Listener got new toot: {}'.format(id))
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
            print("Received a heartbeat from the server!")
            self.receivedHeartbeat = True

    def on_abort(self, status_code):
        logging.warning('Listener got error, status code: {}'.format(status_code))
        return True

logging.info('Init Listener:')
logging.info('  - Toots Folder: \'{}\''.format(tootsFetchSettings['folder']))
logging.info('  - Search String: \'{}\''.format(searchString))

listener = DecarbnowStreamListener(mastodon)

logging.info('Init Toots API File ...')
update()

logging.info('Start Listener ...')
listener.stream_with_reconnection()