# -*- coding: utf-8 -*-
"""Test app error handling."""

from flask import Flask, jsonify
from hookserver.util import _load_github_hooks
from werkzeug.exceptions import ServiceUnavailable
from werkzeug.serving import ThreadedWSGIServer
import pytest
import threading


@pytest.fixture()
def serving_app(request):
    """Create a Flask app and serve it over 8080.

    Destroy the server when the test ends.
    """
    app = Flask(__name__)
    server = ThreadedWSGIServer('127.0.0.1', 8080, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    request.addfinalizer(server.shutdown)
    return app


def test_bad_connection():
    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://0.0.0.0:1234')
    assert (exc.value.description == 'Error reaching GitHub')


def test_github_good(serving_app):
    @serving_app.route('/meta')
    def meta():
        return jsonify({'hooks': ['192.30.252.0/22']})

    network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert network == ['192.30.252.0/22']


def test_bad_structure(serving_app):
    @serving_app.route('/meta')
    def meta():
        return jsonify({})

    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert exc.value.description == 'Error reaching GitHub'


def test_bad_status(serving_app):
    @serving_app.route('/meta')
    def meta():
        return jsonify({'hooks': ['192.30.252.0/22']}), 403

    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert exc.value.description == 'Error reaching GitHub'


def test_bad_headers(serving_app):
    @serving_app.route('/meta')
    def meta():
        headers = {
            'X-RateLimit-Remaining': 0,
        }
        return jsonify({'hooks': ['192.30.252.0/22']}), 403, headers

    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert exc.value.description == 'Error reaching GitHub'


def test_bad_headers(serving_app):
    @serving_app.route('/meta')
    def meta():
        headers = {
            'X-RateLimit-Remaining': 0,
            'X-RateLimit-Reset': 'abc',
        }
        return jsonify({'hooks': ['192.30.252.0/22']}), 403, headers

    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert exc.value.description == 'Error reaching GitHub'


def test_rate_limited(serving_app):
    @serving_app.route('/meta')
    def meta():
        headers = {
            'X-RateLimit-Remaining': 0,
            'X-RateLimit-Reset': 1445929478,
        }
        return jsonify({'hooks': ['192.30.252.0/22']}), 403, headers

    with pytest.raises(ServiceUnavailable) as exc:
        network = _load_github_hooks(github_url='http://127.0.0.1:8080')
    assert (exc.value.description == 'Rate limited from GitHub until '
            'Tue, 27 Oct 2015 07:04:38 GMT')
