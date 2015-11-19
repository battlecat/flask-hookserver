# -*- coding: utf-8 -*-
"""Contains the main Flask app."""

from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, Forbidden
from .util import is_github_ip, check_signature


class HookRoutes(Blueprint):

    """Blueprint containing hooks.

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

    def __init__(self, name='hooks', import_name=__name__, url='/hooks', **kw):
        """Set up the blueprint.

        - Parent constructor
        - Add pre-request hooks
        - Add main URL route
        """
        Blueprint.__init__(self, name, import_name, **kw)

        self._hooks = {}

        @self.before_request
        def validate_ip():
            if current_app.config.get('VALIDATE_IP', True):
                if not is_github_ip(request.remote_addr):
                    raise Forbidden('Requests must originate from GitHub')

        @self.before_request
        def validate_signature():
            if current_app.config.get('VALIDATE_SIGNATURE', True):
                key = current_app.config['KEY']
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
