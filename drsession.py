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


import json
import bottle
import redis
import Cookie


__all__ = ['SessionMiddleware', '__version__']
__version__ = '1.0.0'


class SessionMiddleware(object):
  
  def __init__(self, app, prefix='drsession:', cookie='drsession', env='drsession', redis_kwargs={}, pool_kwargs={}):
    self.app = app
    self.prefix = prefix
    self.cookie = cookie
    self.env = env
    if pool_kwargs is not None:
      connection_pool = redis.ConnectionPool(**pool_kwargs)
      redis_kwargs['connection_pool'] = connection_pool
    self.r = redis.Redis(**redis_kwargs)
  
  def __call__(self, environ, start_response, exec_info=None):
    cookie = Cookie.SimpleCookie()
    cookie.load(environ['HTTP_COOKIE'])
    session_id = cookie[self.cookie].value
    environ[self.env] = Session(self.r, '%s%s' % (self.prefix, session_id))
    return self.app(environ, start_response, exec_info=exec_info)
    

class Session(object):

  def __init__(self, redis_server, base_key):
    self.server = redis_server
    self.base_key = base_key

  def __setitem__(self, key, item):
    return self.server.hset(self.base_key, key, json.dumps(item))

  def __getitem__(self, key):
    v = self.server.hget(self.base_key, key)
    if v is None: raise KeyError(key)
    return json.loads(v)

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
      return json.loads(v)
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
        for k in E: D[k] = json.dumps(E[k])
      else:
        for (k, v) in E: D[k] = json.dumps(v)
    for k in F: D[k] = json.dumps(F[k])
    v = self.server.hmset(self.base_key, D)

  def keys(self):
    return self.server.hkeys(self.base_key)

  def values(self):
    return [json.loads(v) for v in self.server.hvals(self.base_key)]

  def items(self):
    return [(k,json.loads(v)) for k,v in self.server.hgetall(self.base_key).items()]

  def __cmp__(self, d):
    return cmp(dict(self.items()), d)

  def __contains__(self, key):
    return self.has_key(key)

  def __iter__(self):
    return iter(self.keys())


