from flask import Flask, jsonify, render_template
from flask_cors import CORS
from .modules import tweets, log


def create_app(test_config=None):
    app = Flask(__name__)
    cors = CORS(app)

    app.register_blueprint(tweets.bp)
    app.register_blueprint(log.bp)

    @app.route('/')
    def base():
        return render_template('index.html.j2')

    return app
