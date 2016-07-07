import bottle
import drsession

app = drsession.SessionMiddleware(bottle.app())

@bottle.hook('before_request')
def setup_session():
  bottle.request.session = bottle.request.environ.get('drsession')

@bottle.route('/set')
def set():
  bottle.request.session['foo'] = 'bar'

@bottle.route('/get')
def get():
  return bottle.request.session['foo']
  return 'OK'

bottle.run(app=app)

