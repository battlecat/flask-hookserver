from flask import Flask, request
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.security import safe_str_cmp
from functools import wraps
from time import time
import hashlib
import hmac
import ipaddress
import requests


__version__ = '0.1.4'


class timed_memoize(object):
    """Decorator that caches the value of an argumentless function"""
    
    def __init__(self, timeout):
        """Initialize with timeout in seconds"""
        self.timeout = timeout
        self.last_update = None
        self.cache = None
    
    def __call__(self, fn):
        """Create the wrapped function"""
        @wraps(fn)
        def inner():
            if self.last_update is None or time() - self.last_update > self.timeout:
                self.cache = fn()
                self.last_update = time()
            return self.cache
        return inner


@timed_memoize(60) # So we don't get rate limited
def load_github_hooks():
    """Request GitHub's IP block from their API"""
    return requests.get('https://api.github.com/meta').json()['hooks']


def is_github_ip(ip_str):
    """Verify that an IP address is owned by GitHub"""
    ip = ipaddress.ip_address(ip_str)
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    for block in load_github_hooks():
        if ip in ipaddress.ip_network(block):
            return True
    return False


def check_signature(signature, key, data):
    """Compute the HMAC signature and test against a given hash"""
    digest = 'sha1=' + hmac.new(key, data, hashlib.sha1).hexdigest()
    if not hasattr(hmac, 'compare_digest'):
        # Python 2.6
        return safe_str_cmp(digest, signature)
    return hmac.compare_digest(digest, signature)


class HookServer(Flask):

    def __init__(self, import_name, key, num_proxies=None):

        Flask.__init__(self, import_name)

        if num_proxies is not None:
            self.wsgi_app = ProxyFix(self.wsgi_app, num_proxies=num_proxies)

        self.config['KEY'] = key
        self.config['VALIDATE_IP'] = True
        self.config['VALIDATE_HMAC'] = True
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
            return msg, status

        @self.before_request
        def validate_ip():
            if self.config['VALIDATE_IP']:
                ip = request.remote_addr
                # Python 2.x
                if hasattr(str, 'decode'):
                    ip = ip.decode('utf8')
                if not is_github_ip(ip):
                    raise Forbidden('Requests must originate from GitHub')

        @self.before_request
        def validate_hmac():
            if self.config['VALIDATE_HMAC']:
                key = self.config['KEY']
                signature = request.headers.get('X-Hub-Signature')
                data = request.get_data()

                if not signature:
                    raise BadRequest('Missing HMAC signature')

                if not check_signature(signature, key, data):
                    raise BadRequest('Wrong HMAC signature')

        @self.route('/hooks', methods=['POST'])
        def hook():
            event = request.headers.get('X-GitHub-Event')
            guid = request.headers.get('X-GitHub-Delivery')
            data = request.get_json()

            if not event:
                raise BadRequest('No hook given')
            elif not guid:
                raise BadRequest('No event GUID')
            elif not data:
                raise BadRequest('Request body wasn\'t valid JSON')

            if event in self.hooks:
                return self.hooks[event](data, guid)
            else:
                return 'Hook not used'

    def hook(self, hook_name):
        def _wrapper(fn):
            if hook_name not in self.hooks:
                self.hooks[hook_name] = fn
            else:
                raise Exception('%s hook already registered' % hook_name)
            return fn
        return _wrapper
