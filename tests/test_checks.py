# -*- coding: utf-8 -*-
"""Test the checks that must pass for a request to go through."""

from flask.ext.hookserver import Hooks
from werkzeug.contrib.fixers import ProxyFix
import flask
import pytest


@pytest.fixture
def nocheck():
    """Test client for an app that ignores the IP and signature."""
    app = flask.Flask(__name__)
    app.config['DEBUG'] = True
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    return app.test_client()


@pytest.fixture(autouse=True)
def override_github(monkeypatch):
    """Prevent an actual request to GitHub."""
    monkeypatch.delattr('requests.sessions.Session.request')
    monkeypatch.setattr('flask_hookserver.load_github_hooks',
                        lambda: [u'192.30.252.0/22'])


@pytest.fixture
def app():
    app = flask.Flask(__name__)
    app.config['DEBUG'] = True
    Hooks(app)
    return app


def test_ipv4(app):
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['VALIDATE_IP'] = True
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '192.30.252.1'})
    assert rv.status_code == 404

    rv = client.post('/hooks', headers={'X-Forwarded-For': '192.30.252.1'})
    assert rv.status_code == 400

    rv = client.post('/hooks', headers={'X-Forwarded-For': '192.30.251.255'})
    assert b'Requests must originate from GitHub' in rv.data
    assert rv.status_code == 403

    rv = client.post('/hooks', headers={'X-Forwarded-For': '192.31.0.1'})
    assert b'Requests must originate from GitHub' in rv.data
    assert rv.status_code == 403


def test_ipv6(app):
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['VALIDATE_IP'] = True
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01e:fc01'})
    assert rv.status_code == 404

    rv = client.post('/hooks', headers={'X-Forwarded-For': '::ffff:c01e:fc01'})
    assert rv.status_code == 400

    rv = client.post('/hooks', headers={'X-Forwarded-For': '::ffff:c01e:fbff'})
    assert b'Requests must originate from GitHub' in rv.data
    assert rv.status_code == 403

    rv = client.post('/hooks', headers={'X-Forwarded-For': '::ffff:c01f:1'})
    assert b'Requests must originate from GitHub' in rv.data
    assert rv.status_code == 403


def test_ignore_ip(app):
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '192.30.251.255'})
    assert rv.status_code == 404

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01e:fbff'})
    assert rv.status_code == 404


def test_signature(app):
    app.config['GITHUB_WEBHOOKS_KEY'] = b'Some key'
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = True
    client = app.test_client()

    rv = client.post('/hooks', data='{}', content_type='application/json')
    assert b'Missing signature' in rv.data
    assert rv.status_code == 400

    headers = {
        'X-Hub-Signature': 'sha1=e1590250fd7dd7882185062d1ade5bef8cb4319c',
    }
    rv = client.post('/hooks', data='{}', content_type='application/json',
                     headers=headers)
    assert rv.status_code == 400

    headers = {
        'X-Hub-Signature': 'sha1=abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert b'Wrong signature' in rv.data
    assert rv.status_code == 400


def test_ignore_signature(app):
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/')
    assert rv.status_code == 404

    headers = {
        'X-Hub-Signature': 'sha1=abc',
    }
    rv = client.post('/', content_type='application/json', data='{}',
                     headers=headers)
    assert rv.status_code == 404


def test_all_checks(app):
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['GITHUB_WEBHOOKS_KEY'] = b'Some key'
    app.config['VALIDATE_IP'] = True
    app.config['VALIDATE_SIGNATURE'] = True
    client = app.test_client()

    sig = 'e1590250fd7dd7882185062d1ade5bef8cb4319c'
    headers = {
        'X-Forwarded-For': '::ffff:c01e:fc01',
        'X-Hub-Signature': 'sha1=' + sig,
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert rv.status_code == 200


def test_different_url():
    app = flask.Flask(__name__)
    app.config['DEBUG'] = True
    Hooks(app, url='/some_url')

    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    headers = {
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/some_url', content_type='application/json', data='{}',
                     headers=headers)
    assert rv.status_code == 200

    rv = client.post('/hooks')
    assert rv.status_code == 404


def test_missing_hook_data(app):
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert b'Missing header: X-GitHub-Event' in rv.data
    assert rv.status_code == 400

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Event': 'ping',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert b'Missing header: X-GitHub-Delivery' in rv.data
    assert rv.status_code == 400

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='',
                     headers=headers)
    assert b'Missing' not in rv.data
    assert rv.status_code == 400
