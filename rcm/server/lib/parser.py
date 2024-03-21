import inspect
import types
import api
import argparse
import sys
import logging

logger = logging.getLogger('rcmServer' + '.' + __name__)


class CommandParser:
    """
    Class that parses the command line coming from the client
    and call the corresponding server api if found

    To test:
        parser.handle(["--command=config","--build_platform=linux"])
    """

    def __init__(self, protocol):
        self.protocol = protocol
        self.functions = dict()
        parameters = dict()
        help = 'rcm_server commands\n'

        for name, func in inspect.getmembers(api.ServerAPIs):
            if self._is_class_method(name, func):
                f_args = inspect.getfullargspec(func)[0]
                self.functions[str(name)] = (func, f_args)
                help += "\n --command=" + str(name)
                for arg in f_args:
                    if arg != 'self':
                        parameters[arg] = "--" + arg
                        help += " " + parameters[arg] + "=<" + arg + ">"

        self.parser = argparse.ArgumentParser(usage=help)
        self.parser.add_argument("--debug",
                                 type=int,
                                 default=0,
                                 help='set debug level')
        self.parser.add_argument("--command",
                                 default='',
                                 help='set the api command ' + str(self.functions.keys()))
        for parameter in parameters.keys():
            self.parser.add_argument(parameters[parameter],
                                     default='',
                                     help='set the ' + parameter + ' parameter')

    @staticmethod
    def _is_class_method(name, func):
        if sys.version_info >= (3, 0):
            if isinstance(func, types.FunctionType) and name != '__init__':
                return True
            else:
                return False
        else:
            if isinstance(func, types.MethodType) and name != '__init__':
                return True
            else:
                return False

    def handle(self, args=None):
        if args:
            flags = self.parser.parse_args(args).__dict__
            logger.debug("parsing command " + str(args))
        else:
            # if args is not set, read the flags via command line
            flags = self.parser.parse_args().__dict__
            logger.debug("parsing command line")

        if 'command' not in flags:
            logger.error("please specify a command")
            return

        command = flags['command']
        if command == '':
            logger.error("please specify a command")
            return

        if command not in self.functions.keys():
            logger.error("command " + command + " undefined")
            return

        func = self.functions[command][0]
        func_flags = dict()
        # collect all the relevant parameters for the function and pass it
        for parameter in self.functions[command][1]:
            flag = flags.get(parameter, '')
            if flag != '':
                func_flags[parameter] = flag
        func(self.protocol, **func_flags)
