# -*- coding: utf-8 -*-
"""Test app error handling."""

import hookserver
import pytest


def test_500():
    app = hookserver.HookServer(__name__)
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False

    @app.route('/error500')
    def dividebyzero():
        1/0

    with app.test_client() as c:
        rv = c.get('/error500')
        assert rv.data == b'Internal Server Error\n'
        assert rv.status_code == 500
