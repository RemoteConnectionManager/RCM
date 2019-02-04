import inspect
import types
import rcm_protocol_server
import optparse
import sys
import logger_server
import logging

logger = logging.getLogger('rcmServer')


class CommandParser:
    args = ''
    help = 'rcm_server commands\n'
    functions=dict()
    parameters=dict()
    for name,fn in inspect.getmembers(rcm_protocol_server.rcm_protocol):
        if isinstance(fn, types.MethodType) and name != '__init__':
            f_args=inspect.getargspec(fn)[0]
            functions[str(name)]=(fn,f_args)
            help+="\n --command="+str(name)
            for par in f_args :
                if(par != 'self'):
                    parameters[par]= "--"+par
                    help+=" "+parameters[par]+"=<"+par+">"

    parser=optparse.OptionParser(usage=help)
    parser.add_option("--debug", type='int', default=0, help='set debug level')
    parser.add_option("--command",default=False,help='set the api command '+ str(functions.keys()))
    for p in parameters.keys() :
      parser.add_option(parameters[p],default='',help='set the ' + p + ' parameter' )

    def __init__(self,rcm_prot_instance):
         
        self.protocol=rcm_prot_instance

    def handle(self,args=None):
      logger.debug("Command Parser handle")
      if(args):
        (o,a)=CommandParser.parser.parse_args(args)
      else:
        (o,a)=CommandParser.parser.parse_args()
      options=o.__dict__
      logger_server.logger_server.logger_setup(options['debug'])

      fname=options['command']
      if(fname):
        if(fname == ''):
            sys.stdout.write("please specify a command-->"+str(options))
            return
        if(fname in self.functions.keys()):
            myfunc=self.functions[fname][0]
            myargs=dict()
            #collect all the relevant parameters for the function and pass it
            for p in self.functions[fname][1]:
                a=options.get(p,'')
                if(a != ''): myargs[p]=a
            myfunc(self.protocol,**myargs)
        else:
            sys.stdout.write("command " + fname + " undefined" + str(options))
      else:
        logger.error("missing command option " + str(options))


if __name__ == '__main__':
    print("testing rcm_protocol_parser ..................................")
    import dummy_rcm_scheduler
    import rcm_protocol_server
    r=rcm_protocol_server.rcm_protocol(dummy_rcm_scheduler.rcm_server())
    c=CommandParser(r)
    c.handle(["list"])
    c.handle(["--command=config","--build_platform=uffa"])
