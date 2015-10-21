# -*- coding: utf-8 -*-
"""Some helper functions."""

from functools import wraps
from time import time
import hashlib
import hmac
import ipaddress
import requests
import werkzeug.exceptions
import werkzeug.security


class timed_memoize(object):

    """Decorator that caches the value of an argumentless function."""

    def __init__(self, timeout):
        """Initialize with timeout in seconds."""
        self.timeout = timeout
        self.last = None
        self.cache = None

    def __call__(self, fn):
        """Create the wrapped function."""
        @wraps(fn)
        def inner():
            if self.last is None or time() - self.last > self.timeout:
                self.cache = fn()
                self.last = time()
            return self.cache
        return inner


@timed_memoize(60)  # So we don't get rate limited
def load_github_hooks():
    """Request GitHub's IP block from their API."""
    try:
        return requests.get('https://api.github.com/meta').json()['hooks']
    except KeyError:
        # This should not happen if timed_memoize is working correctly
        raise werkzeug.exceptions.ServiceUnavailable('Error reaching GitHub')


def is_github_ip(ip_str):
    """Verify that an IP address is owned by GitHub."""
    if hasattr(ip_str, 'decode'):
        ip_str = ip_str.decode('utf-8')

    ip = ipaddress.ip_address(ip_str)
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    for block in load_github_hooks():
        if ip in ipaddress.ip_network(block):
            return True
    return False


def check_signature(signature, key, data):
    """Compute the HMAC signature and test against a given hash."""
    digest = 'sha1=' + hmac.new(key, data, hashlib.sha1).hexdigest()

    # Covert everything to byte sequences
    if hasattr(digest, 'encode'):
        digest = digest.encode('utf-8')
    if hasattr(signature, 'encode'):
        signature = signature.encode('utf-8')

    if not hasattr(hmac, 'compare_digest'):
        # Python 2.6 doesn't have hmac.compare_digest
        return werkzeug.security.safe_str_cmp(digest, signature)

    return hmac.compare_digest(digest, signature)
