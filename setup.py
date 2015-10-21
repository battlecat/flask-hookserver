# -*- coding: utf-8 -*-
"""Setuptools."""

from setuptools import setup
import re
import sys

version = ''
with open('hookserver/__init__.py') as f:
    version = re.search(r'__version__\s*=\s*\'([\d.]+)\'', f.read()).group(1)

if not version:
    raise RuntimeError('Couldn\'t find version string')

requirements = [
    'Flask>=0.10.1',
    'requests>=2.3.0',
    'Werkzeug>=0.9',
]
if sys.version_info < (3, 3):
    requirements.append('ipaddress>=1.0.6')

setup(
    name='flask-hookserver',
    version=version,
    url='https://github.com/nickfrostatx/flask-hookserver',
    author='Nick Frost',
    author_email='nickfrostatx@gmail.com',
    description='Server for GitHub webhooks using Flask',
    license='MIT',
    packages=['hookserver'],
    install_requires=requirements,
    keywords=['github', 'webhooks', 'flask'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
    ],
)
