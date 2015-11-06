# -*- coding: utf-8 -*-
"""Test direct usage of the blueprint."""

from flask import Flask, jsonify
from hookserver.blueprint import HookRoutes
import pytest


@pytest.fixture
def app():
    server = Flask(__name__)
    server.config['DEBUG'] = True
    server.config['VALIDATE_IP'] = False
    server.config['VALIDATE_SIGNATURE'] = False
    return server


def test_hooks(app):
    blueprint = HookRoutes()
    app.register_blueprint(blueprint)

    @blueprint.hook('ping')
    def ping(data, guid):
        return 'pong'

    headers = {
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    with app.test_client() as client:
        rv = client.post('/hooks', content_type='application/json', data='{}',
                         headers=headers)
        assert rv.data == b'pong'
        assert rv.status_code == 200


def test_register_handler(app):
    blueprint = HookRoutes()
    app.register_blueprint(blueprint)

    def ping(data, guid):
        return 'pong'

    blueprint.register_hook('ping', ping)

    headers = {
        'X-GitHub-Event': 'ping',
        'X-GitHub-Delivery': 'abc',
    }
    with app.test_client() as client:
        rv = client.post('/hooks', content_type='application/json', data='{}',
                         headers=headers)
        assert rv.data == b'pong'
        assert rv.status_code == 200
