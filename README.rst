GitHub webhooks using Flask
###########################

.. image:: https://img.shields.io/travis/nickfrostatx/flask-hookserver.svg
        :target: https://travis-ci.org/nickfrostatx/flask-hookserver

.. image:: https://img.shields.io/pypi/v/flask-hookserver.svg
    :target: https://pypi.python.org/pypi/flask-hookserver

.. image:: https://img.shields.io/pypi/l/flask-hookserver.svg
    :target: https://raw.githubusercontent.com/nickfrostatx/flask-hookserver/master/LICENSE

A tool that receives webhooks from GitHub and passes the data along to a user-defined function. It validates the HMAC hash, and checks that the originating IP address comes from the GitHub IP block.

Example
-------

.. code-block:: python

    from hookserver import HookServer

    app = HookServer(__name__, b'mySecretKey')

    @app.hook('ping')
    def ping(data, guid):
        return 'pong'

    app.run()

num_proxies
-----------

The optional parameter `num_proxies` is used to prevent clients from pretending to be on the GitHub IP block. Set it to the number of proxies you have in front of your WSGI server. See the `Werkzeug documentation <http://werkzeug.pocoo.org/docs/contrib/fixers/#werkzeug.contrib.fixers.ProxyFix>`_ for more info.
