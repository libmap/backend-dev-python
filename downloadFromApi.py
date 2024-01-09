import os
import requests
import json
from lib.shared import authToken

BASE_URL = "https://dev.decarbnow.space"
AUTH_URL = BASE_URL + "/authenticate/"
DOWNLOAD_URL = BASE_URL + "/tweets/"

# Create a session to maintain authentication
session = requests.Session()

# Authenticate using the provided token
auth_response = session.get(AUTH_URL + authToken)
if auth_response.status_code != 200:
    print(f"Authentication failed with status code: {auth_response.status_code}")
    exit()

# Path to the data folder
data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

# Load tweet IDs from fromAPI.json
with open(os.path.join(data_folder, "fromAPI.json"), "r") as json_file:
    tweet_data = json.load(json_file)
    tweet_ids = tweet_data.get("tweets", {}).keys()

# Download files for each tweet ID
for tweet_id in tweet_ids:
    download_url = DOWNLOAD_URL + tweet_id

    # Send request to download the file
    file_response = session.get(download_url)
    if file_response.status_code == 200:
        # Save the file in the data folder
        with open(os.path.join(data_folder, "live", f"{tweet_id}.json"), "wb") as file:
            file.write(file_response.content)
        print(f"Downloaded file for tweet ID {tweet_id}")
    else:
        print(f"Failed to download file for tweet ID {tweet_id} with status code: {file_response.status_code}")

# Close the session
session.close()
