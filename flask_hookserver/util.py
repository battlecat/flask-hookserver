# -*- coding: utf-8 -*-
"""Some helper functions."""

from functools import wraps
from werkzeug.exceptions import ServiceUnavailable
import hashlib
import hmac
import ipaddress
import requests
import time
import werkzeug.security


class timed_memoize(object):

    """Decorator that caches the value of function.

    Does not care about arguments to the function, will still only cache
    one value.
    """

    def __init__(self, timeout):
        """Initialize with timeout in seconds."""
        self.timeout = timeout
        self.last = None
        self.cache = None

    def __call__(self, fn):
        """Create the wrapped function."""
        @wraps(fn)
        def inner(*args, **kwargs):
            if self.last is None or time.time() - self.last > self.timeout:
                self.cache = fn(*args, **kwargs)
                self.last = time.time()
            return self.cache
        return inner


def _load_github_hooks(github_url='https://api.github.com'):
    """Request GitHub's IP block from their API.

    Return the IP network.

    If we detect a rate-limit error, raise an error message stating when
    the rate limit will reset.

    If something else goes wrong, raise a generic 503.
    """
    try:
        resp = requests.get(github_url + '/meta')
        if resp.status_code == 200:
            return resp.json()['hooks']
        else:
            if resp.headers.get('X-RateLimit-Remaining') == '0':
                reset_ts = int(resp.headers['X-RateLimit-Reset'])
                reset_string = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                             time.gmtime(reset_ts))
                raise ServiceUnavailable('Rate limited from GitHub until ' +
                                         reset_string)
            else:
                raise ServiceUnavailable('Error reaching GitHub')
    except (KeyError, ValueError, requests.exceptions.ConnectionError):
        raise ServiceUnavailable('Error reaching GitHub')


# So we don't get rate limited
load_github_hooks = timed_memoize(60)(_load_github_hooks)


def is_github_ip(ip_str):
    """Verify that an IP address is owned by GitHub."""
    if hasattr(ip_str, 'decode'):
        ip_str = ip_str.decode()

    ip = ipaddress.ip_address(ip_str)
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    for block in load_github_hooks():
        if ip in ipaddress.ip_network(block):
            return True
    return False


def check_signature(signature, key, data):
    """Compute the HMAC signature and test against a given hash."""
    if hasattr(key, 'encode'):
        key = key.encode()

    digest = 'sha1=' + hmac.new(key, data, hashlib.sha1).hexdigest()

    # Covert everything to byte sequences
    if hasattr(digest, 'encode'):
        digest = digest.encode()
    if hasattr(signature, 'encode'):
        signature = signature.encode()

    return werkzeug.security.safe_str_cmp(digest, signature)
