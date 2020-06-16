import os
from flask import Blueprint, jsonify, Response, render_template, abort
from lib.shared import base_folder

bp = Blueprint('log', __name__, url_prefix='/log')

files = ['listener', 'init', 'api']

@bp.route('/<string:file>')
@bp.route('/<string:file>/<string:format>')
def logfile(file, format = 'plain'):
    if file not in files:
        abort(404)
    with open(os.path.join(base_folder, 'log/{}.log'.format(file))) as f:
        lines = reversed(f.readlines())
        if format == 'html':
            return render_template('index.log.html.j2', lines = lines, file = file, files = files)
        else:
            return Response(''.join(lines), mimetype='text/plain')
