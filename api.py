from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import json
from datetime import datetime
app = Flask(__name__)
cors = CORS(app)

@app.route('/poi')
@cross_origin()
def list_poi():
    with open('data/first.json', 'r') as f:
        l = json.load(f)

    return jsonify({
        'date': int(datetime.timestamp(datetime.now())),
        'tweets': l
    })
