# -*- coding: utf-8 -*-
"""
Test utility functions used for request validation
"""

from hookserver import is_github_ip, check_signature


def test_correct_ip():
    assert is_github_ip(u'192.30.252.1') == True


def test_mapped_ip():
    assert is_github_ip(u'::ffff:c01e:fc01') == True


def test_bad_ips():
    assert is_github_ip(u'192.30.251.255') == False
    assert is_github_ip(u'192.31.0.1') == False


def test_bad_mapped_ips():
    assert is_github_ip(u'::ffff:c01e:fbff') == False
    assert is_github_ip(u'::ffff:c01f:1') == False


def test_good_signatures():
    key = b'Some key'
    signatures = {
        b'': 'sha1=82821338dd780c9d304011785fc164410a29363e',
        b'hi': 'sha1=5e6d699dd7c8ca40c90d0daa910c5caddef89421',
    }
    for d in signatures:
        assert check_signature(signatures[d], key, d) == True


def test_bad_signatures():
    key = b'Some key'
    signatures = {
        b'': '',
        b'': 'sha1=',
        b'123': 'sha1=',
        b'abc': 'sha1=2346*%#!huteab',
        b'do-re-mi': 'sha1=baby you and me',
    }
    for d in signatures:
        assert check_signature(signatures[d], key, d) == False
