from flask import Flask, jsonify
from flask_cors import CORS
from .modules import tweets, log


def create_app(test_config=None):
    app = Flask(__name__)
    cors = CORS(app)

    app.register_blueprint(tweets.bp)
    app.register_blueprint(log.bp)

    return app
