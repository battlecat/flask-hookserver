# -*- coding: utf-8 -*-
"""Test hook routing."""

from flask.ext.hookserver import Hooks
import flask
import pytest
import json


@pytest.fixture
def app():
    server = flask.Flask(__name__)
    server.config['DEBUG'] = True
    server.config['VALIDATE_IP'] = False
    server.config['VALIDATE_SIGNATURE'] = False
    return server


def post(client, hook, data, guid='abc'):
    headers = {
        'X-GitHub-Event': hook,
        'X-GitHub-Delivery': guid,
    }
    return client.post('/hooks', content_type='application/json',
                       data=json.dumps(data), headers=headers)


def test_hook_not_used(app):
    Hooks(app)

    with app.test_client() as client:
        rv = post(client, 'ping', {})
        assert b'Hook not used'
        assert rv.status_code == 200


def test_ping(app):
    hooks = Hooks(app)

    @hooks.hook('ping')
    def pong(data, guid):
        return 'pong'

    with app.test_client() as client:
        rv = post(client, 'ping', {})
        assert b'pong' in rv.data
        assert rv.status_code == 200


def test_guid(app):
    hooks = Hooks(app)

    @hooks.hook('push')
    def pong(data, guid):
        return 'GUID: ' + guid

    with app.test_client() as client:
        rv = post(client, 'push', {}, guid='abcdef')
        assert b'GUID: abcdef' in rv.data
        assert rv.status_code == 200


def test_too_many_hooks(app):
    hooks = Hooks(app)

    @hooks.hook('ping')
    def pong(data, guid):
        return 'pong'

    with pytest.raises(Exception) as e:
        @hooks.hook('ping')
        def pong2():
            return 'another pong'
    assert 'ping hook already registered' in str(e)
