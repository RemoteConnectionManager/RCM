#
import logging
import re
import os
import time
import copy

import plugin
import utils
from collections import OrderedDict

logger = logging.getLogger('rcmServer' + '.' + __name__)

class Service(plugin.Plugin):


    def __init__(self, *args, **kwargs):
        self.COMMANDS = {'bash': None}
        super(Service, self).__init__(*args, **kwargs)

    def run_preload(self, key='PRELOAD_LINE', substitutions=None):
        self.logger.debug("GENERIC run_preload for service: "+ self.NAME)

        if key in self.templates:
            preload_command = self.templates[key]
            if substitutions:
                preload_command = utils.StringTemplate(preload_command).safe_substitute(substitutions)
            self.logger.info("Running preload command: " + preload_command)
            bash = self.COMMANDS.get('bash', None)
            params = ["-c", preload_command]
            raw_output = bash( *params,
                             output=str)
            self.logger.info("Returned: " + raw_output)
        else:
            self.logger.info("preload command key: " + key + " NOT FOUND")
            for t in self.templates:
                self.logger.debug("plugin template: " + t + "--->" + str(self.templates[t]) + "<--")

    def search_logfile(self, logfile, regex_list=None, regex_list_key='START_REGEX_LIST', wait=1, timeout=0, timeout_key='TIMEOUT'):
        if regex_list == None:
            regex_list = self.templates.get(regex_list_key, [])
        try:
                timeout = timeout  + int(self.templates.get(timeout_key, '10'))
        except:
            timeout = 100

        if logfile and regex_list:
            regex_clist = []
            for regex_string in regex_list:
                self.logger.debug("compiling regex: -->"+ str(regex_string) + "<--")
                regex_clist.append(re.compile(str(regex_string),re.MULTILINE))

            secs = 0
            step = wait
            while (secs < timeout):
                if os.path.isfile(logfile):
                    #print(secs, "logfile:", logfile,)
                    f=open(logfile,'r')
                    with open(logfile, 'r') as f:
                        log_string=f.read()
                    #print("log_string:\n", log_string)
                    for r in regex_clist:
                        x = r.search(log_string)
                        if x:
                            return x.groupdict()
                secs+=step
                time.sleep(step)
            raise Exception("Timeouted (%d seconds) job not correcty running!!!" % (timeout) )
        raise Exception("Unable to search_logfile: %s with regex %s" % (logfile, str(regex_list)))

    def search_port(self, logfile='', timeout=0):
        raise NotImplementedError()



class ScreenService(Service):


    def __init__(self, *args, **kwargs):
        super(ScreenService, self).__init__(*args, **kwargs)

        if 'client_info' in kwargs:
            self.client_info = kwargs['client_info']
            if 'screen_width' in self.client_info and 'screen_height' in self.client_info:
                self.PARAMS['WM'] = self.size_param

    def size_param(self,default_params=None):
        params = OrderedDict()
        if default_params:
            for par in default_params:
                # assign self.client_info['screen_height'] tp params[par]['XSIZE']['max] while getting everythin else
                # from default_params
                params[par] = copy.deepcopy(default_params.get(par, default_params.get('ALL', OrderedDict())))
                for yaml_par_name, info_par_name in [('XSIZE', 'screen_width'), ('YSIZE', 'screen_height')]:
                    tmp = params[par].get(yaml_par_name, OrderedDict())
                    tmp['max'] = self.client_info[info_par_name]
                    params[par][yaml_par_name] = tmp
        return params



class VncService(ScreenService):


    def __init__(self, *args, **kwargs):
        self.COMMANDS = {'bash': None,
                         'vncpasswd': None,
                         'vncserver': None}
        super(VncService, self).__init__(*args, **kwargs)

    def search_port(self, logfile='', timeout=0):
        for t in self.templates:
            self.logger.debug("Searching port, plugin template: "+ t+ "--->"+str(self.templates[t])+"<--")
        groupdict = self.search_logfile(logfile, timeout=timeout)
        res_dict = dict()
        for k in groupdict:
            self.logger.debug("searching port, key: " + k + " ==> " + groupdict[k])
            if k == 'display' :
                res_dict[k] = int(groupdict[k])
                res_dict['port'] =  5900 + int(groupdict[k])
            if k == 'node' :
                # apply nodename substitutions, if defined
                key = 'HOSTNAME_TEMPLATE'
                if key in self.templates:
                    res_dict[k] = utils.StringTemplate(self.templates[key]).safe_substitute({'HOSTNAME': groupdict[k]})
                else:
                    res_dict[k] = groupdict[k]
            if k == 'port' :
                res_dict[k] = int(groupdict[k])

        return res_dict


class TurboVNCServer(VncService):
    def __init__(self, *args, **kwargs):
        self.NAME = "TurboVNC"
        super(TurboVNCServer, self).__init__(*args, **kwargs)


class SystemVNCServer(VncService):
    def __init__(self, *args, **kwargs):
        self.NAME = "SystemVNC"
        super(SystemVNCServer, self).__init__(*args, **kwargs)


class TurboVNCServerCustom(VncService):
    def __init__(self, *args, **kwargs):
        self.NAME = "TurboVNC_custom"
        super(TurboVNCServerCustom, self).__init__(*args, **kwargs)



class Fake(Service):
    def __init__(self, *args, **kwargs):
        self.NAME = "FakeService"
        super(Fake, self).__init__(*args, **kwargs)

