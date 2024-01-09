import os
import logging
import json
from datetime import datetime

from .shared import toots_folder, data_folder, tootsFetchSettings
from .mastodon_auth import get_auth_user

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


def readTootFromFolder(id, folder = tootsFetchSettings['folder']):
    ff = os.path.join(toots_folder, folder)
    with open(os.path.join(ff, '{}.json'.format(id)), 'r') as f:
        return json.load(f)

def writeTootToFolder(toot, folder = tootsFetchSettings['folder']):
    ff = os.path.join(toots_folder, folder)
    with open(os.path.join(ff, '{}.json'.format(toot['id'])), 'w') as f:
        json.dump(toot, f, cls=DateTimeEncoder)

def writeTootToArchive(toot, folder = tootsFetchSettings['folder']):
    ff = os.path.join(toots_folder, folder, "archive")
    with open(os.path.join(ff, '{}.json'.format(toot['id'])), 'w') as f:
        json.dump(toot, f, cls=DateTimeEncoder)

def deleteTootFromFolder(id, folder = tootsFetchSettings['folder']):
    ff = os.path.join(toots_folder, folder)
    os.remove(os.path.join(ff, '{}.json'.format(id)))

def readTootsFromFolder(folder = tootsFetchSettings['folder']):
    ff = os.path.join(toots_folder, folder)
    toots = [readTootFromFolder(f[:-5], folder) for f in os.listdir(ff) if f[-5:] == '.json']
    logging.info('Read {} toots from folder: \'{}\''.format(len(toots), folder))
    return toots


def readTootFromMastodon(id):
    mastodon = get_auth_user()
    logging.info('Reading toot info from Mastodon API: {}'.format(id))
    return mastodon.status(id)

def writeTootsApiJson(data, tootsApiFile = tootsFetchSettings['file']):
    filePath = os.path.join(data_folder, tootsApiFile)
    logging.info('Writing new toots API file: \'{}\''.format(tootsApiFile))
    with open(filePath, 'w') as f:
        json.dump(data, f)

def readTootsApiJson(tootsApiFile = tootsFetchSettings['file']):
    with open(os.path.join(data_folder, tootsApiFile), 'r') as f:
        return json.load(f)
