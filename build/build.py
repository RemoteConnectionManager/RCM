#!/bin/env python

import os
import tempfile
import shutil
import sys


for arg in sys.argv: 
    print "args " + arg

if len(sys.argv) > 1: print 'Custom platfrom: ' + sys.argv[1]

build = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(build)

print "Build dir: ", build
print "Root dir: ", root

#create tmp dir
tmpDir = tempfile.gettempdir()
tmpFile = os.path.join(tmpDir,'rcm_client_tk.spec')
print "Tmp dir: ",tmpDir

if len(sys.argv) > 1:
    #insert exe file name in tmp spec file
    with open(tmpFile, "wt") as out:
        for line in open(os.path.join(root,'spec_files','rcm_client_tk.spec')):
            out.write(line.replace('customPlatform=\'\'', 'customPlatform=\''+ sys.argv[1] +'\''))
else:
    shutil.copyfile(os.path.join(root,'spec_files','rcm_client_tk.spec'), tmpFile)
    
    

os.chdir(tmpDir)
if(sys.platform == 'darwin'):
	os.environ['VERSIONER_PYTHON_PREFER_32_BIT']='1'
	pythoncommand='arch -i386 python '
else:
	pythoncommand='python '
os.system(pythoncommand + os.path.join(root,'PyInstaller','pyinstaller-2.0','utils','Build.py') + ' ' + tmpFile)
