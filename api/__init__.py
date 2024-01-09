from flask import Flask, current_app, render_template, request, session
from flask_cors import CORS
from .modules import toots, log
from .modules.auth import login_exempt
from lib.shared import authToken, secretKey
from datetime import timedelta

def create_app(test_config = None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secretKey
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=100)

    cors = CORS(app)

    app.register_blueprint(toots.bp)
    app.register_blueprint(log.bp)

    @app.route('/')
    def base():
        return render_template('index.html.j2')

    @app.before_request
    def check_auth():
        if not request.endpoint or request.endpoint.rsplit('.', 1)[-1] == 'static':
           return
        view = current_app.view_functions[request.endpoint]
        if getattr(view, 'login_exempt', False):
            return

        if 'loggedIn' in session and session['loggedIn']:
            return

        return "401, Authenticate via /authenticate/TOKEN"

    @app.route('/authenticate/<string:token>')
    @login_exempt
    def authenticate(token):
        if token == authToken:
            session.permanent = True
            session['loggedIn'] = True
            return "Authenticated via /authenticate/TOKEN"
        else:
            return "Invalid token"

    @app.route('/deauthenticate')
    def deauthenticate():
        session['loggedIn'] = False
        return "Deauthenticate"

    return app
