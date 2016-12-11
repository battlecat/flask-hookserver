import os
from flask import Flask
from flask.ext.hookserver import Hooks

app = Flask(__name__)
app.config['GITHUB_WEBHOOKS_KEY'] = 'my_secret_key'

hooks = Hooks(app, url='/hooks')

@hooks.hook('ping')
def ping(data, guid):
    return 'pong'

@hooks.hook('push')
def new_code(data, delivery):
    os.system('sh ~/quokka-env/flask-hookserver/push.sh')   
#    print res  
    print('New push to %s' % data['ref'])
#    return 'Thanks'
   

app.run(host='0.0.0.0',port='8000')
