from flask import Blueprint, jsonify, Response, render_template
from flask_cors import CORS, cross_origin
from datetime import datetime
import json
import logging

from lib.tweets_base import readTweetsApiJson
from lib.Tweet import Tweet
from lib.TweetForest import TweetForest

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

@bp.route('/')
@cross_origin()
def root():
    return jsonify({
        'date': int(datetime.timestamp(datetime.now())),
        'tweets': readTweetsApiJson()
    })

@bp.route('/<int:id>')
def tweet(id):
    t = Tweet.loadFromFile(id)
    return jsonify(t.data)

@bp.route('/tree')
def tree():
    tt = TweetForest.fromFolder()
    return Response(str(tt), mimetype='text/plain')

@bp.route('/info')
def info():
    tweets = readTweetsApiJson()
    stories = {};
    for id, info in tweets.items():
        if 'story' in info:
            storyId = info['story']
            if storyId not in stories:
                stories[storyId] = []
            stories[storyId].append(Tweet.loadFromFile(id))
    return render_template('index.html.j2', stories = stories)
    # tt = TweetForest.fromFolder()
    # return Response(str(tt), mimetype='text/plain')
