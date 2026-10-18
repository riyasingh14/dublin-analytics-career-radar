"""Vercel Flask entrypoint, deliberately independent of Streamlit and private data."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnsupportedMediaType
from career_radar.web_api import dispatch

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024


@app.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.route('/api/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def endpoint():
    try:
        if request.method == 'GET':
            action = request.args.get('action', 'health')
            if action not in {'health', 'bootstrap'}:
                return jsonify(error='Use POST for analytical requests.'), 405
            payload = {}
        else:
            payload = request.get_json()
            if not isinstance(payload, dict):
                raise ValueError('Expected a JSON object.')
            action = payload.get('action')
        return jsonify(dispatch(action, payload))
    except RequestEntityTooLarge:
        return jsonify(error='Request exceeds the 64 KB limit.'), 413
    except (BadRequest, UnsupportedMediaType):
        return jsonify(error='Send a valid JSON object.'), 400
    except (ValueError, TypeError, KeyError):
        # Do not echo applicant notes, descriptions, raw JSON or internal paths.
        return jsonify(error='Invalid input. Check description length, requirement IDs, filters and parameter limits.'), 400


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
