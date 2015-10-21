# -*- coding: utf-8 -*-
"""Contains the main Flask app."""

from flask import Flask, request
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden
from werkzeug.contrib.fixers import ProxyFix
from .util import is_github_ip, check_signature


class HookServer(Flask):

    """The GitHub webhooks app.

    Here is the flow for each post request:
     - If VALIDATE_IP is set, see if the source IP address comes from
       the GitHub IP block (err 403)
     - if VALIDATE_SIGNATURE is set, compute the HMAC signature and
       compare against the provided X-Hub-Signature header (err 400)
     - See if X-GitHub-Event or X-GitHub-Delivery are missing (err 400)
     - Make sure we received valid JSON (err 400)
     - If the supplied hook has been registered, call it with the
       provided data
    """

    def __init__(self, import_name, key=None, num_proxies=None, url='/hooks'):
        """Set up the app.

        - Initial setup (ProxyFix, default config vars)
        - Register error handler
        - Add pre-request hooks
        - Add main URL route
        """
        Flask.__init__(self, import_name)

        if num_proxies is not None:
            self.wsgi_app = ProxyFix(self.wsgi_app, num_proxies=num_proxies)

        self.config['KEY'] = key
        self.config['VALIDATE_IP'] = True
        self.config['VALIDATE_SIGNATURE'] = True
        self.hooks = {}

        @self.errorhandler(400)
        @self.errorhandler(403)
        @self.errorhandler(404)
        @self.errorhandler(500)
        def handle_error(e):
            if isinstance(e, HTTPException):
                msg = e.description
                status = e.code
            else:
                msg = 'Internal server error'
                status = 500
            return msg + '\n', status

        @self.before_request
        def validate_ip():
            if self.config['VALIDATE_IP']:
                if not is_github_ip(request.remote_addr):
                    raise Forbidden('Requests must originate from GitHub')

        @self.before_request
        def validate_signature():
            if self.config['VALIDATE_SIGNATURE']:
                key = self.config['KEY']
                signature = request.headers.get('X-Hub-Signature')
                data = request.get_data()

                if not signature:
                    raise BadRequest('Missing signature')

                if not check_signature(signature, key, data):
                    raise BadRequest('Wrong signature')

        @self.route(url, methods=['POST'])
        def hook():
            event = request.headers.get('X-GitHub-Event', None)
            guid = request.headers.get('X-GitHub-Delivery', None)
            data = request.get_json()

            if event is None:
                raise BadRequest('Missing event')
            elif guid is None:
                raise BadRequest('Missing GUID')

            if event in self.hooks:
                return self.hooks[event](data, guid)
            else:
                return 'Hook not used\n'

    def hook(self, hook_name):
        """Register a function to be called on a GitHub event."""
        def _wrapper(fn):
            if hook_name not in self.hooks:
                self.hooks[hook_name] = fn
            else:
                raise Exception('%s hook already registered' % hook_name)
            return fn
        return _wrapper
