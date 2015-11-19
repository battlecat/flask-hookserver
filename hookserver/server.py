# -*- coding: utf-8 -*-
"""Contains the main Flask app."""

from flask import Flask
from werkzeug.exceptions import HTTPException
from werkzeug.contrib.fixers import ProxyFix
from .blueprint import HookRoutes


class HookServer(Flask):

    """The GitHub webhooks app.

    Create a Flask app with the HookRoutes blueprint
    """

    def __init__(self, import_name, key=None, num_proxies=None, url='/hooks'):
        """Set up the app.

        - Initial setup (ProxyFix, default config vars)
        - Register error handler
        """
        Flask.__init__(self, import_name)

        if num_proxies is not None:
            self.wsgi_app = ProxyFix(self.wsgi_app, num_proxies=num_proxies)

        self.config['KEY'] = key
        self.config.setdefault('VALIDATE_IP', True)
        self.config.setdefault('VALIDATE_SIGNATURE', True)

        self._blueprint = HookRoutes('hooks', import_name, url)
        self.register_blueprint(self._blueprint)

        @self.errorhandler(400)
        @self.errorhandler(403)
        @self.errorhandler(404)
        @self.errorhandler(500)
        @self.errorhandler(503)
        def handle_error(e):
            if isinstance(e, HTTPException):
                msg = e.description
                status = e.code
            else:
                msg = 'Internal Server Error'
                status = 500
            return msg + '\n', status

    def hook(self, hook_name):
        """Pass the function along to the blueprint."""
        def wrapper(fn):
            self._blueprint.register_hook(hook_name, fn)
            return fn
        return wrapper
