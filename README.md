# DRSession
Derek's Redis Session Middleware

## Why?
I started a bottle project with the beaker session example everyone seems to give:

```python
import bottle
from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'ext:memcached',
    'session.url': '127.0.0.1:11211',
    'session.cookie_expires': False,
    'session.auto': True,
    'session.key': 'hvst-session',
    'session.lock_dir': '/tmp/.lock_dir',
}
app = SessionMiddleware(bottle.app(), session_opts)

@bottle.route('/test')
def test():
  s = bottle.request.environ.get('beaker.session')
  s['test'] = s.get('test',0) + 1
  s.save()
  return 'Test counter: %d' % s['test']

bottle.run(app=app)
```

But it didn't quite fit our needs for the following reasons:

1. It's using `memcached` which drops old sessions after a while (and all sessions during restarts).
2. It's serializing/setting the entire session every request (even when no values in the session were set).  This was causing changes to be lost in production due to the obvious race condition.
3. If I'm unable to set a session value, I want an exception, not a silent failure.
4. WTF is up w/ the required lock file?!?

Beaker's session middleware supposedly supports Redis (which would solve the first problem), but the rest remain.  So I wrote this bit of code.

## Hello World

```python
import bottle

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

```

This backs your session object with the Redis server instance running on `localhost` (using a connection pool) and sets `request.session` as the dictionary-like interface.

## Design

### All Changes are Live
There is no `request.session.save()`.

If I call `request.session['foo'] = 'bar'`, it sets it in Redis right then and there.  If Redis is unavailable or throws an exception, you get that exception.  No more "I JUST set that - where the heck did it go?" debugging.

### Don't Write All The Things

If I call `request.session['foo'] = 'bar'`, just write `foo`.

Don't write every value in my entire session every time I set anything.

Definitely don't write every value in my entire session every time I read anything.

### Take Advantage of Redis' Hash Type

Your session id (plus a prefix) is your Redis key.  The keys in your session are keys to the Redis hash type set at your Redis key.  The hash values are `json` encoded strings of the objects in your session.

### Support All the Types

By default DRSession serializes with the python `json` module.  If you wish for a different encoding, pass in new functions to the `loads` and `dumps` parameters of `SessionMiddleware`.

## Documentation

```
>>> help(drsession.SessionMiddleware)
class SessionMiddleware(__builtin__.object)
 |  Methods defined here:
 |  __init__(self, app, 
 |      prefix='drsession:', cookie='drsession', env='drsession', 
 |      redis_server=None, redis_kwargs={},
 |      connection_pool=None, connection_pool_kwargs={},
 |      loads=None, dumps=None)
```

| Option        | Description  |
| ------------- | ------------ |
| `app`         | Any WSGI app object (ie any callable object that takes `environ, start_response, exec_info=None`). |
| `prefix`      | The Redis key prefix.  Default is `'drsession:'`.  If your session id is `abc123` your Redis key will be `'drsession:abc123'`. |
| `cookie` | The HTML cookie storing your session id. |
| `env` | The key  used to store the session object in `bottle.request.environ`. |
| `redis_server` and `redis_kwargs` | If `redis_server` is provided it is used directly.  Else created with `redis.Redis(**redis_kwargs)` |
| `connection_pool` and `connection_pool_kwargs` | If `connection_pool` is provided it is used directly.  Else created with `redis.ConnectionPool(**connection_pool_kwargs)` if `connection_pool_kwargs` is defined.  To not use any connection pooling set `connection_pool_kwargs=None`.  To be "used" means to be added to `redis_kwargs`. |
| `dumps` and `loads` | Serialization and deserialization functions.  Default to `json.dumps` and `json.loads`. |
