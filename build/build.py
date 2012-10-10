#!/bin/env python

import os
import tempfile
import shutil
import sys



build = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(build)

print "Build dir: ", build
print "Root dir: ", root

#create tmp dir
tmpDir = tempfile.gettempdir()
tmpFile = os.path.join(tmpDir,'rcm_client_tk.spec')
print "Tmp dir: ",tmpDir

shutil.copyfile(os.path.join(root,'spec_files','rcm_client_tk.spec'), tmpFile)

os.chdir(tmpDir)
if(sys.platform == 'darwin'):
	os.environ['VERSIONER_PYTHON_PREFER_32_BIT']='1'
	pythoncommand='arch -i386 python '
else:
	pythoncommand='python '
os.system(pythoncommand + os.path.join(root,'PyInstaller','pyinstaller-1.5.1','Build.py') + ' ' + tmpFile)
