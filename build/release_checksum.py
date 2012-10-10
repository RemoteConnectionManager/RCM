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
    result = re.match(r"^RCM_(.*)", exefile)
    if(result):
        myplatform = result.group(1)
        myplatform = myplatform.replace(".exe","")
        myplatform = myplatform.replace(".dmg","")
        url[myplatform]=baseurl+exefile
        print myplatform+" = "+url[myplatform]
        checksum[myplatform]=mychecksum(os.path.join(release_dir,exefile))
        print myplatform+" = "+checksum[myplatform]

#edit configuration file
configurationFile = os.path.join(root,"server", "versionRCM.cfg")
f = open(configurationFile, 'w')
f.write("[checksum]" + '\n')
for checksumKey in checksum.keys():
    f.write(checksumKey+" = "+ checksum[checksumKey] + '\n')
f.write("[url]" + '\n')
for urlKey in url.keys():
    f.write(urlKey+" = "+url[urlKey] + '\n')
f.close()

        
#create tmp dir
