##!./venv/bin/python

import os
import logging
import time
import threading
import argparse
from mastodon import StreamListener

from lib.shared import base_folder, tootsFetchSettings, toots_folder
try:
    from lib.mastodon_auth import get_auth_user
except Exception as e:
    logging.warning(f"Mastodon auth not configured: {e}")
    get_auth_user = None
from lib.mastodon_base import writeTootToFolder, writeTootToArchive, readTootFromFolder, deleteTootFromFolder
from lib.TootForest import TootForest
from lib.bluesky_base import BlueSkyStreamListener

# Parse command line arguments
parser = argparse.ArgumentParser(description='Social Media Listener')
parser.add_argument('--platforms', type=str, default='all',
                    help='Platforms to listen to: all, mastodon, bluesky, or comma-separated list (e.g., mastodon,bluesky)')
parser.add_argument('--mastodon-only', action='store_true', help='Listen only to Mastodon')
parser.add_argument('--bluesky-only', action='store_true', help='Listen only to Bluesky')
args = parser.parse_args()

# Determine which platforms to enable
if args.mastodon_only:
    enable_mastodon = True
    enable_bluesky = False
elif args.bluesky_only:
    enable_mastodon = False
    enable_bluesky = True
elif args.platforms.lower() == 'all':
    enable_mastodon = True
    enable_bluesky = True
else:
    platforms = [p.strip().lower() for p in args.platforms.split(',')]
    enable_mastodon = 'mastodon' in platforms
    enable_bluesky = 'bluesky' in platforms

mastodon = get_auth_user() if get_auth_user and enable_mastodon else None

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

def handle_bluesky_post(bluesky_post):
    """Handle incoming Bluesky posts, converting them to toot format and saving"""
    global existing_ids
    id = str(bluesky_post['id'])
    if keyword in bluesky_post['content']:
        logging.info('Listener got new Bluesky post: {}'.format(id))

        # Check for story threading (same user replying to themselves with libmap link)
        if (bluesky_post.get('in_reply_to_id') and
            bluesky_post.get('in_reply_to_account_id') and
            bluesky_post.get('account', {}).get('acct') == bluesky_post.get('in_reply_to_account_id')):

            # This is a self-reply, check if the parent has a libmap link and is in our collection
            parent_id = str(bluesky_post['in_reply_to_id'])
            if parent_id in existing_ids:
                try:
                    parent_toot = readTootFromFolder(parent_id, tootsFetchSettings['folder'])
                    if keyword in parent_toot.get('content', ''):
                        # Parent has libmap link, this should be part of a story
                        # Find the root of the story by following the chain
                        root_id = parent_id
                        while True:
                            try:
                                root_toot = readTootFromFolder(root_id, tootsFetchSettings['folder'])
                                if (root_toot.get('in_reply_to_id') and
                                    str(root_toot.get('in_reply_to_account_id')) == str(bluesky_post.get('account', {}).get('acct')) and
                                    str(root_toot['in_reply_to_id']) in existing_ids):
                                    root_id = str(root_toot['in_reply_to_id'])
                                else:
                                    break
                            except:
                                break

                        # Add story field to the post before saving
                        bluesky_post['story'] = root_id
                        logging.info('Added Bluesky story field: {} -> {}'.format(id, root_id))
                except Exception as e:
                    logging.warning('Error checking Bluesky story threading: {}'.format(e))

        writeTootToFolder(bluesky_post, tootsFetchSettings['folder'])
        # Update existing_ids immediately to include the new post
        existing_ids.append(id)
        update()

def handle_bluesky_deletion(post_id):
    """Handle Bluesky post deletions - only archive posts we have captured"""
    global existing_ids
    str_status = str(post_id)
    if str_status in existing_ids:
        # This is a post we actually captured and stored
        logging.info('Archiving Bluesky post (id: {})!'.format(str_status))
        toot = readTootFromFolder(str_status, tootsFetchSettings['folder'])
        archive_dir = os.path.join(toots_folder, tootsFetchSettings['folder'], 'archive')
        os.makedirs(archive_dir, exist_ok=True)

        writeTootToArchive(toot, tootsFetchSettings['folder'])
        deleteTootFromFolder(post_id, tootsFetchSettings['folder'])
        # Remove from existing_ids immediately
        existing_ids.remove(str_status)
        update()
    # If post_id not in existing_ids, we silently ignore it (not relevant to us)


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
                logging.warning(f"Error: {e}")
                logging.info("Trying to reconnect after " + str(retry_delay) + " seconds.")
                retry_count += 1
                time.sleep(retry_delay)

    def on_update(self, toot):
        global existing_ids
        if keyword in toot['content']:
            id = str(toot['id'])  # Convert the ID to a string, if it's not already
            logging.info('Listener got new toot: {}'.format(id))

            # Check for story threading (same user replying to themselves with libmap link)
            if (toot.get('in_reply_to_id') and
                toot.get('in_reply_to_account_id') and
                toot.get('account', {}).get('id') == toot.get('in_reply_to_account_id')):

                # This is a self-reply, check if the parent has a libmap link and is in our collection
                parent_id = str(toot['in_reply_to_id'])
                if parent_id in existing_ids:
                    try:
                        parent_toot = readTootFromFolder(parent_id, tootsFetchSettings['folder'])
                        if keyword in parent_toot.get('content', ''):
                            # Parent has libmap link, this should be part of a story
                            # Find the root of the story by following the chain
                            root_id = parent_id
                            while True:
                                try:
                                    root_toot = readTootFromFolder(root_id, tootsFetchSettings['folder'])
                                    if (root_toot.get('in_reply_to_id') and
                                        str(root_toot.get('in_reply_to_account_id')) == str(toot.get('account', {}).get('id')) and
                                        str(root_toot['in_reply_to_id']) in existing_ids):
                                        root_id = str(root_toot['in_reply_to_id'])
                                    else:
                                        break
                                except:
                                    break

                            # Add story field to the toot before saving
                            toot['story'] = root_id
                            logging.info('Added story field: {} -> {}'.format(id, root_id))
                    except Exception as e:
                        logging.warning('Error checking story threading: {}'.format(e))

            writeTootToFolder(toot, tootsFetchSettings['folder'])
            # Update existing_ids immediately to include the new post
            if id not in existing_ids:
                existing_ids.append(id)
            update()

    def on_status_update(self, toot):
        global existing_ids
        if keyword in toot['content']:
            id = str(toot['id'])
            logging.info('Listener got update of toot: {}'.format(id))

            # Check for story threading (same user replying to themselves with libmap link)
            if (toot.get('in_reply_to_id') and
                toot.get('in_reply_to_account_id') and
                toot.get('account', {}).get('id') == toot.get('in_reply_to_account_id')):

                # This is a self-reply, check if the parent has a libmap link and is in our collection
                parent_id = str(toot['in_reply_to_id'])
                if parent_id in existing_ids:
                    try:
                        parent_toot = readTootFromFolder(parent_id, tootsFetchSettings['folder'])
                        if keyword in parent_toot.get('content', ''):
                            # Parent has libmap link, this should be part of a story
                            # Find the root of the story by following the chain
                            root_id = parent_id
                            while True:
                                try:
                                    root_toot = readTootFromFolder(root_id, tootsFetchSettings['folder'])
                                    if (root_toot.get('in_reply_to_id') and
                                        str(root_toot.get('in_reply_to_account_id')) == str(toot.get('account', {}).get('id')) and
                                        str(root_toot['in_reply_to_id']) in existing_ids):
                                        root_id = str(root_toot['in_reply_to_id'])
                                    else:
                                        break
                                except:
                                    break

                            # Add story field to the toot before saving
                            toot['story'] = root_id
                            logging.info('Added story field to updated toot: {} -> {}'.format(id, root_id))
                    except Exception as e:
                        logging.warning('Error checking story threading on update: {}'.format(e))

            writeTootToFolder(toot, tootsFetchSettings['folder'])
            # Update existing_ids immediately to include the new post
            if id not in existing_ids:
                existing_ids.append(id)
            update()

    def on_delete(self, status_id):
        global existing_ids
        str_status = str(status_id)
        if str_status in existing_ids:
            logging.info('Archiving toot (id: {})!'.format(str_status))
            toot = readTootFromFolder(str_status)
            archive_dir = os.path.join(toots_folder, tootsFetchSettings['folder'], 'archive')
            os.makedirs(archive_dir, exist_ok=True)

            writeTootToArchive(toot, tootsFetchSettings['folder'])
            deleteTootFromFolder(status_id, tootsFetchSettings['folder'])
            # Remove from existing_ids immediately
            existing_ids.remove(str_status)
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
logging.info('  - Enabled Platforms: Mastodon={}, Bluesky={}'.format(enable_mastodon, enable_bluesky))

listener = MastodonStreamListener(mastodon) if mastodon and enable_mastodon else None

# Initialize Bluesky listener if enabled
# Use the same keyword as Mastodon for consistency
keywords = [searchString]  # Keep the full search string as one keyword
bluesky_listener = BlueSkyStreamListener(keywords, handle_bluesky_post) if enable_bluesky else None

# Set up deletion callback for Bluesky
if bluesky_listener:
    bluesky_listener.set_deletion_callback(handle_bluesky_deletion)

logging.info('Init Toots API File ...')
update()

logging.info('Start Listeners ...')

# Start Bluesky listener in a separate thread if enabled
bluesky_thread = None
if bluesky_listener:
    bluesky_thread = threading.Thread(target=bluesky_listener.start_stream, daemon=True)
    bluesky_thread.start()
    logging.info('Bluesky listener started in background thread')
else:
    logging.info('Bluesky listener disabled')

# Start Mastodon listener (blocks) if enabled
if listener:
    logging.info('Starting Mastodon listener...')
    try:
        listener.stream_with_reconnection()
    except KeyboardInterrupt:
        logging.info('Shutting down listeners...')
        if bluesky_listener:
            bluesky_listener.stop_stream()
        raise
else:
    logging.info('Mastodon listener disabled')
    if bluesky_listener:
        logging.info('Running with Bluesky only - press Ctrl+C to stop')
        try:
            # Keep the main thread alive when only Bluesky is running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info('Shutting down Bluesky listener...')
            bluesky_listener.stop_stream()
    else:
        logging.error('No listeners enabled! Use --help for usage information.')