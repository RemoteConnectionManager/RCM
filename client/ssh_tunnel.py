import sys

for arg in sys.argv: 
    print arg
portnumber=5900 + int(sys.argv[1])
print "portnumber-->",portnumber
#from subprocess import call
import subprocess
#subprocess.call(["D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe" , "-ssh" , "-L" , str(portnumber) + ":node096:" + str(portnumber) , "cin0118a@login2.plx.cineca.it"])
#myfile=subprocess.Popen("echo Hello World", stdout=subprocess.PIPE, shell=True).stdout
#command="D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe -ssh -m f:\prova\mycommands.txt -L " + str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it"
#command="D:\portable_dev\PortableApps\PuTTYPortable\App\putty/putty.exe -ssh  -L " + str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it"
command="ssh -L" +str(portnumber) + ":node096:" + str(portnumber) + " cin0118a@login2.plx.cineca.it echo pippo; sleep 10000000"
print "executing-->" , command , "<--"
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