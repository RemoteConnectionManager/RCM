import unittest
import uuid
import re
import getpass
from datetime import datetime, timedelta

from client.logic.manager import RemoteConnectionManager
from client.miscellaneous.logger import configure_logger
from client.utils.rcm_enum import Mode


class TestManager(unittest.TestCase):

    def test_newcon_api(self):
        import client.logic.rcm_utils as rcm_utils

        print("vncviewer-->" + rcm_utils.which('vncviewer'))

        remote_connection_manager = RemoteConnectionManager()
        host = 'login.galileo.cineca.it' #marconi o galileo
        user = "a08tra01" #input("User:")
        pswd = "8gwCj7dzTuhSU92N" #getpass.getpass('Password:')
        sessionname = str(uuid.uuid4())
        queues = ["light_2gb_1cor",
                  "medium_8gb_1core",
                  "med_16gb_2core",
                  "alarge_32gb_4core",
                  "xtralarge_64gb_8c",
                  "zfull_120gb_16c"]

        state = ["pending", "valid", "killing"]

        remote_connection_manager.login_setup(host=host, remoteuser=user, password=pswd)
        print("open sessions on " + host)
        out = remote_connection_manager.list()
        out.write(2)

        session = remote_connection_manager.newconn(queue='light_2gb_1cor',
                                                    geometry='1024x968',
                                                    sessionname=sessionname,
                                                    vnc_id='fluxbox_turbovnc_vnc')

        remote_connection_manager.vncsession(session)
        out = remote_connection_manager.list()
        out.write(2)

    #   #'created' (140376348444016) = {str} '20180627-14:29:09'
        #'display' (140376348444240) = {str} '1'
        #'file' (140376348361592) = {str} ''
        #'jobid' (140376348444072) = {str} '95553.io01'
    #   #'node' (140376348361368) = {str} 'node168' \d\d\d
    #   #'nodelogin' (140376348380464) = {str} 'login.galileo.cineca.it'
        #'otp' (140376348443792) = {str} ''
    #   #'session name' (140376348439088) = {str} uuid
    #BUG#'sessionid' (140376348420592) = {str} 'a08tra01-pbs-8' [1-10]
    #   #'sessiontype' (140376348420720) = {str} 'pbs'
    #   #'state' (140376348444128) = {str} 'valid'
    #   #'timeleft' (140376348439280) = {str} '12:00:00'
#DIPENDE#'tunnel' (140376348443904) = {str} 'y'
    #   #'username' (140376348377136) = {str} 'a08tra01'
        #'vncpassword' (140376348406128) = {str} 'bc4df1a9bfa87305'
    #   #'walltime' (140376348421616) = {str} '12:00:00'
        #__len__ = {int} 16

        created = datetime.strptime(session.hash['created'],"%Y%m%d-%H:%M:%S")
        now = datetime.now()

        self.assertTrue(re.search("([0-9]{8}\-)(([0-9]{2}\:){2})([0-9]{2})", session.hash['created']))
        self.assertTrue(created - timedelta(minutes=2) < now or created + timedelta(minutes=2) > now)

        self.assertTrue(re.search("(node)([0-9]{1,3})", session.hash['node']))
        self.assertEqual(session.hash['nodelogin'],host)
        self.assertEqual(session.hash['session name'], sessionname)
        self.assertTrue(session.hash['sessionid'][:-1] == '{0}-{1}-'.format(user,session.hash['sessiontype'])
                        and
                        re.search(".*([1-9]|(10))$", session.hash['sessionid']))
        self.assertEqual(session.hash['sessiontype'], "pbs")
        self.assertTrue(session.hash['state'] in state)
        self.assertEqual(session.hash['tunnel'], "y")
        self.assertEqual(session.hash['username'], user)
        self.assertTrue(datetime.strptime(session.hash['timeleft'], "%H:%M:%S")
                        <= datetime.strptime(session.hash['walltime'], "%H:%M:%S"))

        print("created session -->",
              session.hash['sessionid'],
              "<- display->",
              session.hash['display'],
              "<-- node-->",
              session.hash['node'])

        remote_connection_manager.kill(session)
        out = remote_connection_manager.list()
        out.write(2)

    def test_vnccipher(self):
        from client.logic.cipher import RCMCipher
        rcm_cipher = RCMCipher()
        vncpassword = rcm_cipher.vncpassword
        self.assertEqual(vncpassword, rcm_cipher.decrypt(rcm_cipher.encrypt(vncpassword)))


if __name__ == '__main__':
    configure_logger(mode=Mode.TEST, debug=False)
    unittest.main(verbosity=2)
