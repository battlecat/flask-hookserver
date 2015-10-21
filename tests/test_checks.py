# -*- coding: utf-8 -*-
"""Test the checks that must pass for a request to go through."""

import hookserver
import pytest


@pytest.fixture
def nocheck():
    """Test client for an app that ignores the IP and signature"""
    app = hookserver.HookServer(__name__)
    app.config['DEBUG'] = True
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    return app.test_client()


def test_ipv4():
    """Make sure it returns a 404 instead of 403"""
    app = hookserver.HookServer(__name__, num_proxies=1)
    app.config['VALIDATE_IP'] = True
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '192.30.252.1'})
    assert rv.status_code == 404

    rv = client.post('/', headers={'X-Forwarded-For': '192.30.251.255'})
    assert rv.status_code == 403
    assert b'Requests must originate from GitHub' in rv.data

    rv = client.post('/', headers={'X-Forwarded-For': '192.31.0.1'})
    assert rv.status_code == 403
    assert b'Requests must originate from GitHub' in rv.data


def test_num_proxies():
    app = hookserver.HookServer(__name__, num_proxies=2)
    assert app.wsgi_app.__class__.__name__ == 'ProxyFix'


def test_ipv6():
    app = hookserver.HookServer(__name__, num_proxies=1)
    app.config['VALIDATE_IP'] = True
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01e:fc01'})
    assert rv.status_code == 404

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01e:fbff'})
    assert rv.status_code == 403
    assert b'Requests must originate from GitHub' in rv.data

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01f:1'})
    assert rv.status_code == 403
    assert b'Requests must originate from GitHub' in rv.data


def test_ignore_ip():
    app = hookserver.HookServer(__name__, num_proxies=1)
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
    client = app.test_client()

    rv = client.post('/', headers={'X-Forwarded-For': '192.30.251.255'})
    assert rv.status_code == 404

    rv = client.post('/', headers={'X-Forwarded-For': '::ffff:c01e:fbff'})
    assert rv.status_code == 404


def test_signature():
    app = hookserver.HookServer(__name__, b'Some key')
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = True
    client = app.test_client()

    rv = client.post('/', data='{}', content_type='application/json')
    assert rv.status_code == 400
    assert b'Missing signature' in rv.data

    headers = {
        'X-Hub-Signature': 'sha1=e1590250fd7dd7882185062d1ade5bef8cb4319c',
    }
    rv = client.post('/', data='{}', content_type='application/json',
                     headers=headers)
    assert rv.status_code == 404

    headers = {
        'X-Hub-Signature': 'sha1=abc',
    }
    rv = client.post('/',  content_type='application/json', data='{}',
                     headers=headers)
    assert rv.status_code == 400
    assert b'Wrong signature' in rv.data


def test_ignore_signature():
    app = hookserver.HookServer(__name__)
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


def test_all_checks():
    app = hookserver.HookServer(__name__, b'Some key', num_proxies=1)
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


def test_bad_method(nocheck):
    client = nocheck

    rv = client.get('/hooks')
    assert rv.status_code == 405


def test_different_url():
    app = hookserver.HookServer(__name__, url='/some_url')
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


def test_missing_hook_data(nocheck):
    client = nocheck

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert b'Missing event' in rv.data
    assert rv.status_code == 400

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Event': 'ping',
    }
    rv = client.post('/hooks', content_type='application/json', data='{}',
                     headers=headers)
    assert b'Missing GUID' in rv.data
    assert rv.status_code == 400

    rv = client.post('/hooks')
    headers = {
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    rv = client.post('/hooks', content_type='application/json', data='',
                     headers=headers)
    assert b'The browser' in rv.data
    assert rv.status_code == 400
