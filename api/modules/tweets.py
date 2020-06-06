from flask import Blueprint, jsonify, Response
from flask_cors import CORS, cross_origin
from datetime import datetime
import json

from lib.tweets import readTweetsApiJson
from lib.TweetTree import TweetTree
from lib.shared import tweetsFetchSettings

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

@bp.route('/')
@cross_origin()
def l():
    return jsonify({
        'date': int(datetime.timestamp(datetime.now())),
        'tweets': readTweetsApiJson(tweetsFetchSettings['file'])
    })

@bp.route('/tree')
def t():
    tt = TweetTree.fromFolder(tweetsFetchSettings['folder'])
    return Response(str(tt), mimetype='text/plain')
