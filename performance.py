import timeit

def time_it(stmt):
  setup = '''
import drsession
app = drsession.SessionMiddleware(None, prefix='drsession-test:')
session = app._build_session('abc123')
  '''
  number = 20000
  print 'TESTING:', stmt
  seconds = timeit.timeit(stmt, setup=setup, number=number)
  print number, 'loops took', seconds, 'seconds (%.3fms per loop)' % (seconds/number*1000)
  print 

if __name__=='__main__':
  print
  print '--==[ DRSession ]==--'
  print
  print 'Hitting a local Redis server.'
  print 'All data changes are live.'
  print
  time_it("session['foo'] = 'bar' # set a value")
  time_it("session['foo'] # read a value")
  time_it("'foo' in session # does a value exist?")
  time_it("del session['foo'] # remove a value")
  time_it("session.save() # doesn't do anything")

