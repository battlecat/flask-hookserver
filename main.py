from flask import Flask
from flask.ext.hookserver import Hooks

app = Flask(__name__)
app.config['GITHUB_WEBHOOKS_KEY'] = 'my_secret_key'

hooks = Hooks(app, url='/hooks')

@hooks.hook('ping')
def ping(data, guid):
    return 'pong'

app.run('0.0.0.0')
