# -*- coding: utf-8 -*-
"""This module contains the main extension object."""

from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, Forbidden
from .util import is_github_ip, check_signature


class Hooks(object):

    """Main extension class.

    The flow of each post request
     - If VALIDATE_IP is set, see if the source IP address comes from
       the GitHub IP block (err 403)
     - if VALIDATE_SIGNATURE is set, compute the HMAC signature and
       compare against the provided X-Hub-Signature header (err 400)
     - See if X-GitHub-Event or X-GitHub-Delivery are missing (err 400)
     - Make sure we received valid JSON (err 400)
     - If the supplied hook has been registered, call it with the
       provided data
    """

    def __init__(self, app=None, **kwargs):
        """Optionally, initialize the app."""
        self._hooks = {}
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, url='/hooks'):
        """Register the URL route to the application."""
        app.config.setdefault('VALIDATE_IP', True)
        app.config.setdefault('VALIDATE_SIGNATURE', True)

        @app.route(url, methods=['POST'])
        def hook():
            if app.config['VALIDATE_IP']:
                if not is_github_ip(request.remote_addr):
                    raise Forbidden('Requests must originate from GitHub')

            if app.config['VALIDATE_SIGNATURE']:
                key = current_app.config['GITHUB_WEBHOOKS_KEY']
                signature = request.headers.get('X-Hub-Signature')

                if hasattr(request, 'get_data'):
                    # Werkzeug >= 0.9
                    payload = request.get_gata()
                else:
                    payload = request.data

                if not signature:
                    raise BadRequest('Missing signature')

                if not check_signature(signature, key, payload):
                    raise BadRequest('Wrong signature')

            event = request.headers.get('X-GitHub-Event')
            guid = request.headers.get('X-GitHub-Delivery')
            if not event:
                raise BadRequest('Missing header: X-GitHub-Event')
            elif not guid:
                raise BadRequest('Missing header: X-GitHub-Delivery')

            if hasattr(request, 'get_json'):
                # Flask >= 0.10
                data = request.get_json()
            else:
                data = request.json

            if event in self._hooks:
                return self._hooks[event](data, guid)
            else:
                return 'Hook not used\n'

    def register_hook(self, hook_name, fn):
        """Register a function to be called on a GitHub event."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = fn
        else:
            raise Exception('%s hook already registered' % hook_name)

    def hook(self, hook_name):
        """Return a decorator that calls register_hook."""
        def wrapper(fn):
            self.register_hook(hook_name, fn)
            return fn
        return wrapper
