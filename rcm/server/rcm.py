#!/bin/env python
import pickle
import json
import datetime
import sys
import os
import logging

logger = logging.getLogger('RCM.protocol')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

format_default = 'pickle'
if sys.version_info >= (3, 0):
    format_default = 'json'

serverOutputString = "server output->"


class rcm_session:
    def __init__(self,
                 fromstring='',
                 fromfile='',
                 file='',
                 sessionname='',
                 state='',
                 node='',
                 tunnel='',
                 sessiontype='',
                 nodelogin='',
                 display='',
                 jobid='',
                 sessionid='',
                 username='',
                 walltime='',
                 otp='',
                 vncpassword=''
                 ):

        self.hash = {
            'file': '',
            'session name': '',
            'state': '',
            'node': '',
            'tunnel': '',
            'sessiontype': '',
            'nodelogin': '',
            'display': '',
            'jobid': '',
            'sessionid': '',
            'username': '',
            'walltime': '00:00:00',
            'timeleft': '00:00:00',
            'otp': '',
            'vncpassword': ''
        }

        if fromfile != '':
            with open(fromfile, 'r') as content_file:
                fromstring = content_file.read()
            if fromstring[0] == '(':
                logger.debug("Using pickle for rcm_session from file: " + fromfile)
                self.hash = pickle.load(open(fromfile, "rb"))
            elif fromstring[0] == '{':
                logger.debug("Using json for rcm_session from file: " + fromfile)
                self.hash = json.load(open(fromfile, "r"))
            self.hash['file'] = fromfile
        elif fromstring != '':
            if fromstring[0] == '(':
                logger.debug("Using pickle for rcm_session from string: " + fromstring[0])
                self.hash = pickle.loads(fromstring.encode('utf-8'))
            elif fromstring[0] == '{':
                logger.debug("Using json for rcm_session from string: " + fromstring[0])
                self.hash = json.loads(fromstring)
        else:
            self.hash = {
                'file': file,
                'session name': sessionname,
                'state': state,
                'node': node,
                'tunnel': tunnel,
                'sessiontype': sessiontype,
                'nodelogin': nodelogin,
                'display': display,
                'jobid': jobid,
                'sessionid': sessionid,
                'username': username,
                'walltime': walltime,
                'timeleft': walltime,
                'otp': otp,
                'vncpassword': vncpassword
            }
            self.hash['created'] = datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")

    def serialize(self, file, format=format_default):
        logger.debug("Using " + format + " for rcm_session.serialize on file " + file)
        if format == 'pickle':
            pickle.dump(self.hash, open(file, "wb"))
        elif format == 'json':
            json.dump(self.hash, open(file, 'w'), ensure_ascii=False, sort_keys=True, indent=4)

    def get_string(self, format=format_default):
        logger.debug("Using " + format + " for rcm_session.get_string on file ")
        if format == 'pickle':
            return pickle.dumps(self.hash)
        elif format == 'json':
            return json.dumps(self.hash)
        elif format == 'json_indent':
            return json.dumps(self.hash, indent=4)

    def write(self, outstream=sys.stdout):
        logger.debug("Write session rcm_session.write")
        outsring = self.get_string()
        outstream.write(serverOutputString)
        outstream.write(outsring)
        outstream.flush()


class rcm_sessions:
    def __init__(self, fromstring='', fromfile='', sessions=None):
        self._array = []
        if fromfile != '':
            if format_default == 'pickle':
                self._array = pickle.load(open(fromfile, "rb"))
            elif format_default == 'json':
                self._array = json.load(open(fromfile, "r"))
        elif fromstring != '':
            if fromstring[0] == '(':
                logger.debug("Using pickle for rcm_sessions from string: " + fromstring[0])
                old_sessions = pickle.loads(fromstring.encode('utf-8'))
                for s in old_sessions:
                    self._array.append(s.hash)
            elif format_default == 'json':
                logger.debug("Using json for rcm_sessions from string: " + fromstring[0])
                hashes = json.loads(fromstring)
                for h in hashes:
                    self._array.append(h)
        elif sessions:
            self._array = sessions

    def serialize(self, file, format):
        logger.debug("Using " + format + " for rcm_sessions.serialize on file: " + file)
        if format == 'pickle':
            pickle.dump(self._array, open(file, "wb"))
        elif format == 'json':
            json.dump(self._array, open(file, 'w'), ensure_ascii=False, sort_keys=True, indent=4)

    def get_string(self, format=format_default):
        logger.debug("Using " + format + " for rcm_sessions.get_string ")
        if format == 'pickle':
            old_sessions = []
            for s in self._array:
                old_sess = rcm_session()
                old_sess.hash = s
                old_sessions.append(old_sess)
            return pickle.dumps(old_sessions)
        elif format == 'json':
            return json.dumps(self._array)

    def add_session(self, new_session):
        present = False
        for hash in self._array:
            if str(hash) == str(new_session.hash):
                logger.debug("Skipping duplicate session " + str(new_session.hash))
                present = True
                break
        if not present:
            self._array.append(new_session.hash)

    def get_sessions(self):
        out_sess = []
        for h in self._array:
            s = rcm_session()
            s.hash = h
            out_sess.append(s)
        return out_sess

    def write(self, outstream=sys.stdout):
        logger.debug("Write sessions rcm_sessions.write ")
        outsring = self.get_string()
        outstream.write(serverOutputString)
        outstream.write(outsring)
        outstream.flush()

 
class rcm_config:
    def __init__(self, fromstring='', fromfile=''):
        if fromfile != '':
            if format_default == 'pickle':
                self.config = pickle.load(open(fromfile, "rb"))
            elif format_default == 'json':
                self.config = json.load(open(fromfile, "r"))
        elif fromstring != '':
            if fromstring[0] == '(':
                logger.debug("Using pickle for rcm_config from string: " + fromstring[0])
                self.config = pickle.loads(fromstring.encode('utf-8'))
            elif format_default == 'json':
                self.config = json.loads(fromstring)
        else:
            self.config = {'version': {'checksum': '', 'url': ''},
                           'queues': dict(),
                           'vnc_commands': dict()}
        
    def set_version(self, check, url):
        logger.debug("set_version")
        self.config['version']['checksum'] = check
        self.config['version']['url'] = url
        
    def get_version(self):
        logger.debug("get_version")
        return (self.config.get('version', dict()).get('checksum', ''),
                self.config.get('version', dict()).get('url', ''))

    def add_queue(self, queue, info=''):
        logger.debug("add_queue")
        self.config['queues'][queue] = info

    def add_vnc(self, vnc, entry=None):
        logger.debug("add_vnc")
        if not entry:
            entry = (vnc, '')
        self.config['vnc_commands'][vnc] = entry

    def get_string(self, format=format_default):
        logger.debug("Using " + format + " for rcm_config.get_string ")
        if format == 'pickle':
            return pickle.dumps(self.config)
        elif format == 'json':
            return json.dumps(self.config)

    def serialize(self, file='', format=format_default):
        logger.debug("Using " + format + " for rcm_config.serialize on file " + file)

        if file != '':
            if format == 'pickle':
                pickle.dump(self.config, open(file, "wb"))
            elif format == 'json':
                json.dump(self.config, open(file, 'w'), ensure_ascii=False, sort_keys=True, indent=4)
        else:
            sys.stdout.write(serverOutputString + self.get_string())

    def pretty_print(self):
        logger.debug("pretty_print: version checksum: " +
                     self.config['version']['checksum'] +
                     ' url:' + self.config['version']['url'])
        for queue in self.config['queues']:
            logger.debug("queue " + queue + " info: " + self.config['queues'][queue])
        for vnc in sorted(self.config['vnc_commands'].keys()):
            logger.debug("vnc command: " + vnc + " info:" + str(self.config['vnc_commands'][vnc]))
