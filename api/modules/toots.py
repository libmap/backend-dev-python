from datetime import datetime
import logging
import json

from flask import Blueprint, jsonify, Response, render_template, abort
from flask_cors import cross_origin
from .auth import login_exempt

from lib.mastodon_base import readTootsApiJson
from lib.Toot import Toot
from lib.TootForest import TootForest

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

@bp.route('/')
@cross_origin()
@login_exempt
def root():
    # Read the current tweets from the API or other source
    current_tweets = readTootsApiJson()

    # Read additional tweets from file_tweets.json
    try:
        with open('data/file_tweets.json', 'r') as file:
            file_tweets_data = json.load(file)
            # Check if the data is a dictionary
            if isinstance(file_tweets_data, dict):
                # If the current tweets are also a dictionary, update it
                if isinstance(current_tweets, dict):
                    current_tweets.update(file_tweets_data)
                # If the current tweets are a list, convert the dictionary to a list and extend it
                elif isinstance(current_tweets, list):
                    current_tweets.extend(file_tweets_data.values())
                else:
                    raise ValueError("The current tweets are neither a list nor a dictionary.")
            else:
                raise ValueError("The contents of file_tweets.json are not a dictionary")
    except FileNotFoundError:
        logging.error("The file file_tweets.json was not found.")
    except json.JSONDecodeError:
        logging.error("The file file_tweets.json does not contain valid JSON.")
    except ValueError as e:
        logging.error(e)

    # Return the combined data as a JSON response
    return Response(json.dumps({
        'date': int(datetime.timestamp(datetime.now())),
        'tweets': current_tweets
    }), mimetype='application/json')


@bp.route('/<int:id>')
def tweet(id):
    tweet = Toot.loadFromFile(id)
    return jsonify(tweet.data)

@bp.route('/forest')
def forest_show():
    return render_template('forest.html.j2', forest = TootForest.fromFolder())
    #return Response(str(forest), mimetype='text/plain')

@bp.route('/forest/renew')
def forest_create():
    logging.warning('Manual invocation of creating forest!')
    forest = TootForest.fromFolder()
    forest.saveApiJson()

    # Read the current tweets from the API or other source
    current_tweets = readTootsApiJson()

    # Read additional tweets from file_tweets.json
    try:
        with open('data/file_tweets.json', 'r') as file:
            file_tweets_data = json.load(file)
            # Check if the data is a dictionary
            if isinstance(file_tweets_data, dict):
                # If the current tweets are also a dictionary, update it
                if isinstance(current_tweets, dict):
                    current_tweets.update(file_tweets_data)
                # If the current tweets are a list, convert the dictionary to a list and extend it
                elif isinstance(current_tweets, list):
                    current_tweets.extend(file_tweets_data.values())
                else:
                    raise ValueError("The current tweets are neither a list nor a dictionary.")
            else:
                raise ValueError("The contents of file_tweets.json are not a dictionary")
    except FileNotFoundError:
        logging.error("The file file_tweets.json was not found.")
    except json.JSONDecodeError:
        logging.error("The file file_tweets.json does not contain valid JSON.")
    except ValueError as e:
        logging.error(e)

    # Return the combined data as a JSON response
    return Response(json.dumps(current_tweets), mimetype='application/json')

@bp.route('/add/<int:id>')
def add(id):
    logging.warning('Manual invocation of adding tweet (id: {})!'.format(id))
    tweet = Toot.loadFromMastodon(id)
    tweet.save()
    # renew forest
    forest = TootForest.fromFolder()
    forest.saveApiJson()
    return jsonify({
        'message': 'added',
        'tweet': {
            'id': id,
            'data': tweet.data
        }
    })

@bp.route('/delete/<int:id>')
def delete(id):
    logging.warning('Manual invocation of deleting tweet (id: {})!'.format(id))
    tweet = Toot.loadFromFile(id)
    tweet.delete()
    # renew forest
    forest = TootForest.fromFolder()
    forest.saveApiJson()
    return jsonify({
        'message': 'deleted',
        'tweet': {
            'id': id,
            'data': tweet.data
        }
    })

@bp.route('/all')
def all():
    tweets = Toot.loadFromFolder()
    tweets.sort(key = lambda x: x.getDateTime(), reverse = True)
    # [Toot(i) for i in tweets]
    return render_template('all.html.j2', tweets = tweets)

@bp.route('/stories')
def info():
    tweets = readTootsApiJson()
    stories = {};
    for id, info in tweets.items():
        if 'story' in info:
            storyId = info['story']
            if storyId not in stories:
                stories[storyId] = []
            stories[storyId].append(Toot.loadFromFile(id))
    return render_template('stories.html.j2', stories = stories)
