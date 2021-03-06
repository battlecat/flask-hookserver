Flask-Hookserver9
=====================

.. image:: https://travis-ci.org/nickfrostatx/flask-hookserver.svg?branch=master
    :target: https://travis-ci.org/nickfrostatx/flask-hookserver?branch=master

.. image:: https://coveralls.io/repos/github/nickfrostatx/flask-hookserver/badge.svg?branch=master
    :target: https://coveralls.io/github/nickfrostatx/flask-hookserver?branch=master

.. image:: https://readthedocs.org/projects/flask-hookserver/badge/?version=latest
    :target: https://flask-hookserver.readthedocs.org/en/latest/

.. image:: https://img.shields.io/pypi/v/flask-hookserver.svg
    :target: https://pypi.python.org/pypi/flask-hookserver

.. image:: https://img.shields.io/pypi/l/flask-hookserver.svg
    :target: https://raw.githubusercontent.com/nickfrostatx/flask-hookserver/master/LICENSE

GitHub webhooks using Flask.

This tool receives webhooks from GitHub and passes the data along to a
user-defined function. It validates the HMAC signature, and checks that the
originating IP address comes from the GitHub IP block.

Supports Flask >= 0.9

Installation
------------

.. code-block:: bash

    $ sudo yum install openssl-devel
    $ sudo yum install libffi-devel
    $ pip install Flask-Hookserver

Usage
-----

.. code-block:: python

    from flask import Flask
    from flask.ext.hookserver import Hooks

    app = Flask(__name__)
    app.config['GITHUB_WEBHOOKS_KEY'] = 'my_secret_key'

    hooks = Hooks(app, url='/hooks')

    @hooks.hook('ping')
    def ping(data, guid):
        return 'pong'

    app.run(host='0.0.0.0',port='8000')

And there we go! ``localhost:8000/hooks`` will now accept GitHub webhook
events.

Another Usage
-----

Switch to your destination repo

create a file push.sh in this repo only with content:

.. code-block:: python

    #! /bin/bash

    sudo git pull

screen python ~/flask-hookserver/main.py

edit your webhook config with http://xxxx.xxxx:8000/hooks and only for push events option

it is done.

Config
------

Signature and IP validation are both optional, but turned on by default.  They
can each be turned off with a config flag.

.. code-block:: python

    app = HookServer(__name__)
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False

If ``VALIDATE_SIGNATURE`` is set to ``True``, you need to supply the secret key
in ``app.config['GITHUB_WEBHOOKS_KEY']``.

Exceptions
----------

If anything goes wrong, a regular ``HTTPException`` will be raised. Possible
errors include:

- 400: Some headers are missing
- 400: The request body isn't valid JSON
- 400: The signature is missing or incorrect
- 403: The request originated from an invalid IP address
- 503: Could not download the valid webhooks IP block from GitHub
