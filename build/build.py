#!/bin/env python

import os
import tempfile
import shutil



build = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(build)

print "Build dir: ", build
print "Root dir: ", root

#create tmp dir
tmpDir = tempfile.gettempdir()
tmpFile = os.path.join(tmpDir,'crv_client_tk.spec')
print "Tmp dir: ",tmpDir

shutil.copyfile(os.path.join(root,'spec_files','crv_client_tk.spec'), tmpFile)

os.chdir(tmpDir)
os.environ['VERSIONER_PYTHON_PREFER_32_BIT']='1'
os.system('python '+ os.path.join(root,'PyInstaller','pyinstaller-1.5.1','Build.py') + ' ' + tmpFile)
