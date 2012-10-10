#!/bin/env python

import os
import tempfile
import shutil
import re
import hashlib




def mychecksum(file):
    fh = open(file, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
    m.update(data)
    return m.hexdigest()

build = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(build)
baseurl="https://hpc-forge.cineca.it/svn/RemoteGraph/trunk/build/dist/Releases/"

print "Build dir: ", build
print "Root dir: ", root

url=dict()
checksum=dict()
release_dir=os.path.join(build,"dist","Releases")
for exefile in os.listdir(release_dir):
    print exefile
    result = re.match(r"^RCM_(.*)$|.exe$", exefile)
    if(result):
        myplatform = result.group(1)
        url[myplatform]=baseurl+exefile
        print myplatform+" = "+url[myplatform]
        checksum[myplatform]=mychecksum(os.path.join(release_dir,exefile))
        print myplatform+" = "+checksum[myplatform]

        
#create tmp dir
