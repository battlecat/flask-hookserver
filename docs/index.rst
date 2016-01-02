Flask-Hookserver
================

.. module:: flask.ext.hookserver

Support GitHub webhooks with Flask.

Installation
------------

Install the extension with the following command:

.. code-block:: bash

    $ pip install Flask-Hookserver

Configuration
-------------

Webhook handlers are managed using a ``Hook`` instance:

.. code-block:: python

    from flask import Flask
    from flask.ext.hookserver import Hooks

    app = Flask(__name__)
    app.config['GITHUB_WEBHOOKS_KEY'] = 'xxxxxxxx'

    # Request checking options
    app.config['VALIDATE_IP'] = False
    app.config['VALIDATE_SIGNATURE'] = True

    hooks = Hooks(app, url='/desired/webhooks/path')

Flask-Hookserver uses the following configuration variables:

======================= ========================================
``VALIDATE_IP``         Set to ``False`` to skip source IP
                        address checking. (default: ``True``)
``VALIDATE_SIGNATURE``  Set to ``False`` to skip HMAC signature
                        checking. (default: ``True``)
``GITHUB_WEBHOOKS_KEY`` Your secret key on GitHub. This can be
                        found in your repository's Webhooks &
                        Services settings. Only required if
                        ``VALIDATE_SIGNATURE`` is on.
======================= ========================================

Usage
-----

You use the ``hook`` decorator to handle a particular GitHub event.

.. code-block:: python

    @hooks.hook('ping')
    def ping(data, delivery):
        print(data['zen'])
        return 'pong'


    @hooks.hook('push')
    def new_code(data, delivery):
        print('New push to %s' % data['ref'])
        return 'Thanks'

Errors
------

If something goes wrong with a request, a regular
:class:`~werkzeug.exceptions.HTTPException` will be raised with one of the following status codes:

=== =========================================================
400 Missing headers (``X-Hub-Signature``, ``X-GitHub-Event``,
    or ``X-GitHub-Delivery``)
400 Bad JSON data.
400 ``X-Hub-Signature`` is missing or incorrect
403 The request didn't originate from GitHub's network
503 Error trying to ask GitHub for its IP block
=== =========================================================


API Reference
-------------

.. autoclass:: Hooks
   :members:

.. autofunction:: load_github_hooks
