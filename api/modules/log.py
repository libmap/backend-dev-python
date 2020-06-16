import os
from flask import Blueprint, jsonify, Response, render_template
from lib.shared import base_folder

bp = Blueprint('log', __name__, url_prefix='/log')

@bp.route('/listener')
def listener():
    with open(os.path.join(base_folder, 'log/listener.log')) as f:
        return Response(f.read(), mimetype='text/plain')

@bp.route('/api')
def api():
    with open(os.path.join(base_folder, 'log/api.log')) as f:
        return Response(f.read(), mimetype='text/plain')
