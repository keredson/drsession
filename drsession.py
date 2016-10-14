#
# The MIT License (MIT)
# Copyright (c) 2016 Derek Anderson
# https://github.com/keredson/drsession
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.
#


import base64, datetime, os
try:
  import Cookie as cookies
except ImportError:
  import http.cookies as cookies



__all__ = ['SessionMiddleware', '__version__']
__version__ = '1.1.5'


class SessionMiddleware(object):
  
  def __init__(self, app, 
      prefix='drsession:', 
      cookie='drsession', 
      env='drsession', 
      redis_server=None, 
      redis_kwargs={}, 
      connection_pool=None, 
      connection_pool_kwargs={},
      loads=None,
      dumps=None,
      gen_session_id=None):
    import redis
    self.app = app
    self.prefix = prefix
    self.cookie = cookie
    self.env = env
    self.loads = loads
    self.dumps = dumps
    self.gen_session_id = gen_session_id
    if self.gen_session_id is None:
      def gen_session_id():
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
      self.gen_session_id = gen_session_id
    if connection_pool is None:
      if connection_pool_kwargs is not None:
        connection_pool = redis.ConnectionPool(**connection_pool_kwargs)
        redis_kwargs['connection_pool'] = connection_pool
    else:
      redis_kwargs['connection_pool'] = connection_pool
    if redis_server:
      self.redis_server = redis_server
    else:
      self.redis_server = redis.Redis(**redis_kwargs)
  
  def _build_session(self, session_id):
    return Session(self.redis_server, '%s%s' % (self.prefix, session_id), loads=self.loads, dumps=self.dumps)
  
  def __call__(self, environ, start_response, exec_info=None):
    cookie_data = environ.get('HTTP_COOKIE')
    if cookie_data is not None:
      cookie = cookies.SimpleCookie()
      cookie.load(cookie_data)
      session_cookie = cookie.get(self.cookie)
    else:
      session_cookie = None
    if session_cookie:
      session_id = cookie[self.cookie].value
      save_cookie = False
    else:
      session_id = self.gen_session_id()
      save_cookie = True
    environ[self.env] = self._build_session(session_id)
    def session_start_response(status, headers, exec_info=None):
      if save_cookie:
        c = cookies.SimpleCookie()
        c[self.cookie] = session_id
        c[self.cookie]['expires'] = (datetime.datetime.now() + datetime.timedelta(days=10*365)).strftime("%a, %d-%b-%Y %H:%M:%S PST")
        header, value = c.output().split(' ', 1)
        header = header.rstrip(':')
        headers.append((header, value))
      if exec_info is None:
        return start_response(status, headers)
      else:
        return start_response(status, headers, exec_info)
    if exec_info is None:
      return self.app(environ, session_start_response)
    else:
      return self.app(environ, session_start_response, exec_info)
    

class Session(object):

  def __init__(self, redis_server, base_key, loads=None, dumps=None):
    self.server = redis_server
    self.base_key = base_key
    if loads is None:
      import json
      self.loads = json.loads
    if dumps is None:
      import json
      self.dumps = json.dumps

  def __setitem__(self, key, item):
    return self.server.hset(self.base_key, key, self.dumps(item).encode("utf-8"))

  def __getitem__(self, key):
    v = self.server.hget(self.base_key, key)
    if v is None: raise KeyError(key)
    return self.loads(v.decode("utf-8"))

  def __repr__(self):
    return '%s<key=%s>' % (self.__class__.__name__, repr(self.base_key))

  def __len__(self):
    return self.server.hlen(self.base_key)

  def __delitem__(self, key): 
    return self.server.hdel(self.base_key, key)

  def clear(self):
    return self.destroy()

  def destroy(self):
    v = self.server.delete(self.base_key)

  def copy(self):
    raise NotImplementedError()

  def has_key(self, key):
    return self.server.hexists(self.base_key, key)

  def get(self, key, d=None):
    v = self.server.hget(self.base_key, key)
    if v is None: return d
    try:
      return self.loads(v.decode("utf-8"))
    except ValueError:
      return d

  def pop(self, key, d=None):
    v = self.get(key, d)
    del self[key]
    return v

  def update(self, *args, **F):
    D = {}
    if args and len(args)>0:
      E = args[0]
      if hasattr(E,'keys'):
        for k in E: D[k] = self.dumps(E[k]).encode("utf-8")
      else:
        for (k, v) in E: D[k] = self.dumps(v).encode("utf-8")
    for k in F: D[k] = self.dumps(F[k]).encode("utf-8")
    v = self.server.hmset(self.base_key, D)

  def keys(self):
    return [k.decode("utf-8") for k in self.server.hkeys(self.base_key)]

  def values(self):
    return [self.loads(v.decode("utf-8")) for v in self.server.hvals(self.base_key)]

  def items(self):
    return [(k.decode("utf-8"),self.loads(v.decode("utf-8"))) for k,v in self.server.hgetall(self.base_key).items()]

  def __cmp__(self, d):
    return cmp(dict(self.items()), d)

  def __contains__(self, key):
    return self.has_key(key)

  def __iter__(self):
    return iter(self.keys())

  def save(self):
    # nothing to be done - just for compat.
    pass


