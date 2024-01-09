from mastodon import Mastodon
import json
from datetime import datetime
import os
import shutil
from lib.mastodon_auth import get_auth_user

from lib.shared import base_folder, tootsFetchSettings, toots_folder

# Define the URL you want to check for in the messages
keyword = tootsFetchSettings['listen'] + '/@'

# Define the path for the data folder and archive subfolder
data_folder = os.path.join(toots_folder, tootsFetchSettings['folder'])

archive_folder = os.path.join(data_folder, "archive")

# Ensure the data and archive folders exist
os.makedirs(data_folder, exist_ok=True)
os.makedirs(archive_folder, exist_ok=True)

# Get a list of existing message IDs in the data folder
existing_ids = [filename.split(".")[0] for filename in os.listdir(data_folder) if filename.endswith(".json")]

# Create an instance of Mastodon
mastodon = get_auth_user()

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

# Search for messages containing the target URL
search_results = mastodon.search(keyword)

# Check each search result for the target URL
for status in search_results['statuses']:
    # Generate a unique filename using ID
    message_id = str(status['id'])
    filename = f'{message_id}.json'
    filepath = os.path.join(data_folder, filename)

    # Save the relevant information to a JSON file
    with open(filepath, 'w') as output_file:
        json.dump(status, output_file, cls=DateTimeEncoder)

    print(f'Message with ID {message_id} saved to {filepath}')

    # Remove the ID from the existing IDs list if found
    if message_id in existing_ids:
        existing_ids.remove(message_id)

# Move any remaining files in the data folder to the archive folder
for message_id in existing_ids:
    filename = f'{message_id}.json'
    filepath = os.path.join(data_folder, filename)
    archive_filepath = os.path.join(archive_folder, filename)
    shutil.move(filepath, archive_filepath)
    print(f'Message with ID {message_id} moved to archive folder')
