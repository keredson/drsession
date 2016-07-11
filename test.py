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


import unittest
import drsession


class TestDRSession(unittest.TestCase):

  def setUp(self):
    def fake_app(environ, start_response, exec_info=None):
      self.session = environ['drsession']
      self.session.destroy()
    self.app = drsession.SessionMiddleware(fake_app, prefix='drsession-test:')
    self.app({'HTTP_COOKIE': 'drsession=abc123;'}, None)

  def test_string(self):
    self.session['foo'] = 'bar'
    self.assertEqual(self.session['foo'], 'bar')

  def test_list(self):
    self.session['foo'] = ['bar']
    self.assertEqual(self.session['foo'], ['bar'])

  def test_dict(self):
    self.session['foo'] = {'bar':'woot'}
    self.assertEqual(self.session['foo'], {'bar':'woot'})

  def test_None(self):
    self.session['foo'] = None
    self.assertEqual(self.session['foo'], None)

  def test_keyerror(self):
    with self.assertRaises(KeyError):
      v = self.session['foo']

  def test_default(self):
    self.assertEqual(self.session.get('foo'), None)
    self.assertEqual(self.session.get('foo','bar'), 'bar')
    
  def test_repr(self):
    self.assertEqual(repr(self.session), "Session<key='drsession-test:abc123'>")
    
  def test_len(self):
    self.session['foo'] = 'bar'
    self.session['foo2'] = 'bar2'
    self.assertEqual(len(self.session), 2)

  def test_del(self):
    self.session['foo'] = 'bar'
    self.assertEqual(self.session['foo'], 'bar')
    del self.session['foo']    
    self.assertEqual(self.session.get('foo'), None)

  def test_clear(self):
    self.session['foo'] = 'bar'
    self.assertEqual(len(self.session), 1)
    self.session.clear()
    self.assertEqual(len(self.session), 0)

  def test_destroy(self):
    self.session['foo'] = 'bar'
    self.assertEqual(len(self.session), 1)
    self.session.destroy()
    self.assertEqual(len(self.session), 0)

  def test_in(self):
    self.session['foo'] = 'bar'
    self.assertTrue('foo' in self.session)
    self.assertTrue(self.session.has_key('foo'))

  def test_pop(self):
    self.session['foo'] = 'bar'
    self.assertEqual(len(self.session), 1)
    self.assertEqual(self.session.pop('foo'), 'bar')
    self.assertEqual(len(self.session), 0)

  def test_update_dict(self):
    self.session['foo'] = 'bar'
    self.session.update({'foo':'BAR', 'foo2':'bar2'})
    self.assertEqual(self.session['foo'], 'BAR')
    self.assertEqual(self.session['foo2'], 'bar2')

  def test_update_list(self):
    self.session['foo'] = 'bar'
    self.session.update([('foo','BAR'), ('foo2','bar2')])
    self.assertEqual(self.session['foo'], 'BAR')
    self.assertEqual(self.session['foo2'], 'bar2')

  def test_update_kwargs(self):
    self.session['foo'] = 'bar'
    self.session.update(foo='BAR', foo2='bar2')
    self.assertEqual(self.session['foo'], 'BAR')
    self.assertEqual(self.session['foo2'], 'bar2')

  def test_keys(self):
    self.session['foo'] = 'bar'
    self.assertEqual(self.session.keys(), ['foo'])

  def test_values(self):
    self.session['foo'] = 'bar'
    self.assertEqual(self.session.values(), ['bar'])

  def test_items(self):
    self.session['foo'] = 'bar'
    self.assertEqual(self.session.items(), [('foo','bar')])

  def test_no_cookie(self):
    self.app({}, None)


if __name__ == '__main__':
    unittest.main()


