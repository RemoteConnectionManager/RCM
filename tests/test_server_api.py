import unittest
import uuid
import getpass
import datetime

from client.logic.manager import RemoteConnectionManager
import client.logic.rcm_utils as rcm_utils

class TestManager(unittest.TestCase):

    def test_newcon_api(self):
        print("vncviewer-->" + rcm_utils.which('vncviewer'))

        remote_connection_manager = RemoteConnectionManager()
        host = 'login.galileo.cineca.it' #marconi o galileo
        user = "a------1" #input("User:")
        pswd = "8--------------N" #getpass.getpass('Password:')
        sessionname = str(uuid.uuid4())

        remote_connection_manager.login_setup(host=host, remoteuser=user, password=pswd) #missing 1 required positional argument: 'remoteuser'
        print("open sessions on " + host)
        out = remote_connection_manager.list()
        out.write(2)

        session = remote_connection_manager.newconn(queue='light_2gb_1cor',
                                                    geometry='1024x968',
                                                    sessionname=sessionname,
                                                    vnc_id='fluxbox_turbovnc_vnc')

        #'created' (140376348444016) = {str} '20180627-14:29:09'
        #'display' (140376348444240) = {str} '1'
        #'file' (140376348361592) = {str} ''
        #'jobid' (140376348444072) = {str} '95553.io01'
        #'node' (140376348361368) = {str} 'node168'
    #   #'nodelogin' (140376348380464) = {str} 'login.galileo.cineca.it'
        #'otp' (140376348443792) = {str} ''
    #   #'session name' (140376348439088) = {str} uuid
        #'sessionid' (140376348420592) = {str} 'a------1-pbs-8'
   #BUG #'sessiontype' (140376348420720) = {str} 'pbs'
        #'state' (140376348444128) = {str} 'valid'
        #'timeleft' (140376348439280) = {str} '12:00:00'
    #   #'tunnel' (140376348443904) = {str} 'y'
    #   #'username' (140376348377136) = {str} 'a------1'
        #'vncpassword' (140376348406128) = {str} 'bc4df1a9bfa87305'
        #'walltime' (140376348421616) = {str} '12:00:00'
        #__len__ = {int} 16

        print(session.hash['created'])
        print(datetime.datetime.now())

        self.assertEqual(session.hash['nodelogin'],host)
        self.assertEqual(session.hash['session name'], sessionname)
        self.assertEqual(session.hash['tunnel'], "y")
        self.assertEqual(session.hash['sessiontype'], "pbs") #deve essere slurm
        self.assertEqual(session.hash['username'], user)
        #self.assertEqual(session.has['vncpassword'])

        print("created session -->",
              session.hash['sessionid'],
              "<- display->",
              session.hash['display'],
              "<-- node-->",
              session.hash['node'])

        remote_connection_manager.vncsession(session)
        out = remote_connection_manager.list()
        out.write(2)

        remote_connection_manager.kill(session)
        out = remote_connection_manager.list()
        out.write(2)

if __name__ == '__main__':
    unittest.main()
