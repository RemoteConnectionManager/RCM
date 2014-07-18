import sys
import os
import types
import inspect

sys.path.append( os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ) , "server"))

def dec2(fn):
    name=fn.func_name
    code=fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
    print "inside_decorator "+inspect.stack()[0][3]+" function->"+name,
    print "argcount->",argcount, " argnames-->",argnames

    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kw):
        print "calling "+name+" argnames->",argnames
        ret=fn(*args, **kw)
        print "returning",ret
        return ret
    return wrapper

import rcm



for name,fn in inspect.getmembers(rcm.rcm_protocol):
    if isinstance(fn, types.UnboundMethodType):
        setattr(rcm.rcm_protocol, name, dec2(fn))

if __name__ == '__main__':
    def prex(command='',commandnode=''):
        print "node "+commandnode+" "+ command

    for i in ['uno','due','tre']:
      def myfunc(command):
          prex(command,i)
      r=rcm.rcm_protocol(clientfunc=myfunc)
      r.config('mia build platform '+i)

#class rcm_protocol_client(rcm.rcm_protocol):
