#!/bin/env python

import os
import tempfile
import shutil
import sys

DISTPATH=os.path.join(os.path.dirname(os.path.abspath(__file__)),'dist','Releases')
print "---------------->",DISTPATH

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
pythoncommand='python '
#disabledif(sys.platform == 'darwin'):
#disabled	os.environ['VERSIONER_PYTHON_PREFER_32_BIT']='1'
#disabled	pythoncommand='arch -i386 python '
os.system(pythoncommand + os.path.join(root,'PyInstaller','PyInstaller-3.0','pyinstaller.py') + ' --distpath='+ DISTPATH + ' ' + tmpFile)
