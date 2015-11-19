# -*- coding: utf-8 -*-
"""Test utility functions used for request validation."""

from hookserver.util import timed_memoize, is_github_ip, check_signature
from time import sleep, time


def test_timed_memoize():
    i = [0]

    @timed_memoize(0.2)
    def get_i():
        return i[0]

    assert get_i() == 0
    i[0] = 1
    assert get_i() == 0
    sleep(0.1)
    assert get_i() == 0
    sleep(0.15)
    assert get_i() == 1


def test_correct_ip():
    assert is_github_ip('192.30.252.1') == True


def test_ip_decoding():
    assert is_github_ip(b'192.30.252.1') == True
    assert is_github_ip(u'192.30.252.1') == True


def test_mapped_ip():
    assert is_github_ip('::ffff:c01e:fc01') == True


def test_bad_ips():
    assert is_github_ip('192.30.251.255') == False
    assert is_github_ip('192.31.0.1') == False


def test_bad_mapped_ips():
    assert is_github_ip('::ffff:c01e:fbff') == False
    assert is_github_ip('::ffff:c01f:1') == False


def test_good_signatures():
    key = b'Some key'
    signatures = {
        b'': u'sha1=82821338dd780c9d304011785fc164410a29363e',
        b'hi': u'sha1=5e6d699dd7c8ca40c90d0daa910c5caddef89421',
        b'hi': b'sha1=5e6d699dd7c8ca40c90d0daa910c5caddef89421',
    }
    for d in signatures:
        assert check_signature(signatures[d], key, d) == True


def test_unicode_key():
    key = u'Some key'
    data = b'hi'
    check = u'sha1=5e6d699dd7c8ca40c90d0daa910c5caddef89421'
    assert check_signature(check, key, data)


def test_bad_signatures():
    key = b'Some key'
    signatures = {
        b'': b'',
        b'': u'sha1=',
        b'123': b'sha1=',
        b'abc': u'sha1=2346*%#!huteab',
        b'do-re-mi': b'sha1=baby you and me',
    }
    for d in signatures:
        assert check_signature(signatures[d], key, d) == False
