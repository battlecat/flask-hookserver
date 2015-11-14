flask-hookserver
================

.. image:: https://img.shields.io/travis/nickfrostatx/flask-hookserver.svg
    :target: https://travis-ci.org/nickfrostatx/flask-hookserver

.. image:: https://img.shields.io/coveralls/nickfrostatx/flask-hookserver.svg
    :target: https://coveralls.io/github/nickfrostatx/flask-hookserver

.. image:: https://img.shields.io/pypi/v/flask-hookserver.svg
    :target: https://pypi.python.org/pypi/flask-hookserver

.. image:: https://img.shields.io/pypi/l/flask-hookserver.svg
    :target: https://raw.githubusercontent.com/nickfrostatx/flask-hookserver/master/LICENSE

GitHub webhooks using Flask.

This tool receives webhooks from GitHub and passes the data along to a
user-defined function. It validates the HMAC hash, and checks that the
originating IP address comes from the GitHub IP block.

Installation
------------

.. code-block:: bash

    $ pip install flask-hookserver

Usage
-----

.. code-block:: python

    from hookserver import HookServer

    app = HookServer(__name__, key=b'mySecretKey', num_proxies=1, url='/hooks')

    @app.hook('ping')
    def ping(data, guid):
        return 'pong'

    app.run()

The ``HookServer`` constructor takes the following parameters:

* **key** - Byte sequence containing your shared secret key. This is required if ``VALIDATE_SIGNATURE`` is on

* **num_proxies** - If you're using a reverse proxy, this is required to correctly identify the client's IP address. Only really necessary if ``VALIDATE_IP`` is on. See the `Werkzeug documentation <http://werkzeug.pocoo.org/docs/contrib/fixers/#werkzeug.contrib.fixers.ProxyFix>`_ for more info.

* **url** (default ``'/hooks'``) - The URI that GitHub will make the POST request to (for example, ``https://repo.yourserver.com/hooks``)

Blueprint
---------

You can also add GitHub webhooks to an existing Flask application.

.. code-block:: python

    from hookserver import HookRoutes
    from flask import Flask

    app = Flask(__name__)
    app.config['KEY'] = b'mySecretKey'

    # ... Add all your other routes to app

    webhooks = HookRoutes()
    app.register_blueprint(webhooks)

    @webhooks.hook('ping')
    def ping(data, guid):
        return 'pong'

    app.run()

Note that you'll need to manually set the ``KEY`` config variable if you want
to validate the HMAC signatures.

Config
------

Signature and IP validation are both optional, but turned on by default.  They
can each be turned off with a config flag.

.. code-block:: python

    app = HookServer(__name__)
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = False
