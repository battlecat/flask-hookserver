# -*- coding: utf-8 -*-
"""Test hook routing."""

import hookserver
import pytest
import json


@pytest.fixture
def app():
    server = hookserver.HookServer(__name__)
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
    client = app.test_client()
    rv = post(client, 'ping', {})
    assert rv.status_code == 200
    assert b'Hook not used'


def test_ping(app):

    @app.hook('ping')
    def pong(data, guid):
        return 'pong'

    client = app.test_client()
    rv = post(client, 'ping', {})
    assert rv.status_code == 200
    assert b'pong' in rv.data


def test_guid(app):

    @app.hook('push')
    def pong(data, guid):
        return 'GUID: ' + guid

    client = app.test_client()
    rv = post(client, 'push', {}, guid='abcdef')
    assert rv.status_code == 200
    assert b'GUID: abcdef' in rv.data


def test_too_many_hooks(app):

    @app.hook('ping')
    def pong(data, guid):
        return 'pong'

    with pytest.raises(Exception) as e:
        @app.hook('ping')
        def pong2():
            return 'another pong'
    assert 'ping hook already registered' in str(e)
