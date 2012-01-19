import sys
import os 
from optparse import OptionParser
import getpass
import subprocess


parser = OptionParser()
#parser = argparse.ArgumentParser(description='Remote vnc connection wrapper')
parser.add_option('-d','--display', dest='display_num',  action='store', 
                type="int", default=10,
                help='set the diaplay num to connect to (default 10)')
parser.add_option('-u','--user', dest='username',  action='store', 
                type="string", default="cin0118a",
                help='set the user  (default cin0118a)')
parser.add_option('-p','--proxy', dest='proxynode',  action='store', 
                type="string", default="login2.plx.cineca.it",
                help='set the proxynode  (default login2.plx.cineca.it)')

parser.add_option('-t','--target', dest='targetnode',  action='store', 
                type="string", default="node096",
                help='set the target visualization node  (default node096)')

(options, args) = parser.parse_args()

print options, args

config=dict()
config['win32']=("PLINK.EXE"," -ssh")

for arg in sys.argv: 
    print arg
	
basedir = os.path.dirname(os.path.abspath(__file__))
sshexe = os.path.join(basedir,"external",sys.platform,"bin",config[sys.platform][0])
print "uuu",os.path.abspath(__file__),os.path.dirname(os.path.abspath(__file__))
if os.path.exists(sshexe) :
    command = sshexe + config[sys.platform][1]
else:
    command = "ssh"

passwd=getpass.getpass("Get password for" + options.username + "@" + options.proxynode + "-->")

print "got passwd-->",passwd

command = command + " -pw "+passwd

remoterun = command + " " + options.username + "@" + options.proxynode + " module avail"
print "executing-->" , remoterun , "<--"
out=subprocess.check_call( remoterun)  
print "returned--->",out
portnumber=5900 + int(options.display_num)
print "portnumber-->",portnumber

command=command + " -L " +str(portnumber) + ":"+options.targetnode+":" + str(portnumber) + " " + options.username + "@" + options.proxynode + " sh $HOME/; sleep 10000000"
print "executing-->" , command , "<--"
#from subprocess import call
#subprocess.call(["D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe" , "-ssh" , "-L" , str(portnumber) + ":node096:" + str(portnumber) , "cin0118a@login2.plx.cineca.it"])
#myfile=subprocess.Popen("echo Hello World", stdout=subprocess.PIPE, shell=True).stdout
#command="D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe -ssh -m f:\prova\mycommands.txt -L " + str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it"
#command="D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe -ssh  -L " + str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it"
#command="ssh -L" +str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it echo pippo; sleep 10000000"
#print "executing-->" , command , "<--"
#myprocess=subprocess.Popen(command , stdout=subprocess.PIPE, shell=True)
#myprocess=subprocess.Popen(command , bufsize=1, shell=True)
myprocess=subprocess.Popen(command , bufsize=1, stdout=subprocess.PIPE, shell=True)
while True:
   o = myprocess.stdout.readline()
   if o == '' and myprocess.poll() != None: break
   print "output from process---->"+o.strip()+"<---"
   if o.strip() == 'pippo' :
	vnccommand="D:\\portable_dev\\tools\\TurboVNC\\vncviewer localhost:" +sys.argv[1]
	print "starting vncviewer-->"+vnccommand+"<--"
	myprocess1=subprocess.Popen(vnccommand , bufsize=1, stdout=subprocess.PIPE, shell=True)

#	subprocess.call("D:\portable_dev\tools\TurboVNC\vncviewer localhost:" +sys.argv[1] , shell=True) 

#call(["D:\portable_dev\tools\TurboVNC\vncviewer" , "localhost:" +sys.argv[1] ])
#call(["dir"])

#D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe -ssh -m f:\prova\mycommands.txt -L 5940:node096:5940 cin0118a@login2.plx.cineca.it