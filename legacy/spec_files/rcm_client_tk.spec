# -*- mode: python -*-
import sys
import platform
import hashlib
import subprocess
import zipfile

rcmVersion = "1.2."
customPlatform=''

ROOTPATH=os.path.dirname(os.path.dirname(os.path.abspath(HOMEPATH)))
print "---------------->", os.path.abspath(HOMEPATH)
print "---------------->",ROOTPATH

svninfo = ''
myprocess = subprocess.Popen(["svn", "info", ROOTPATH],stdout=subprocess.PIPE)
(myout,myerr)=myprocess.communicate()
for line in myout.splitlines():
	if "URL: " in line:
		svninfo = line[5:]
		break
		
print "SVN info URL: ", svninfo
baseurl = svninfo + "/build/dist/Releases/"
    

#add revision to rcm version 
myprocess = subprocess.Popen(["svnversion",ROOTPATH],stdout=subprocess.PIPE)
(myout,myerr)=myprocess.communicate()

print "revision number:" + str(myout)
rcmVersion = rcmVersion + str(myout)
rcmVersion = rcmVersion.rstrip()


outFile = 'RCM_'
myplatform=sys.platform + '_' + platform.architecture()[0]
file_suffix=""

if(sys.platform == 'win32'):
    data_files=[('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/vncviewer.exe', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','vncviewer.exe'), 'DATA'),('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/PLINK.EXE', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','PLINK.EXE'), 'DATA')]
    file_suffix=".exe"
elif sys.platform.startswith('darwin'):
    data_files=Tree(os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','vncviewer_java'), prefix='external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/vncviewer_java')
else:
    data_files=[('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/vncviewer', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','vncviewer'), 'DATA')]
    if sys.platform.startswith('linux'):
        myplatform += '_' + platform.linux_distribution()[0] + '_' + platform.linux_distribution()[1]
        
if(customPlatform):
    outFile += customPlatform
    myplatform = customPlatform
else:
    outFile += myplatform 
outFile += file_suffix

print "Building ----> ",outFile

print "------------->" , data_files

versionFileName = os.path.join(ROOTPATH, 'build','dist', 'build_platform.txt')
versionfile = open(versionFileName,"w")
versionfile.write(myplatform + '\n')
versionfile.write(rcmVersion)
versionfile.close()
data_files.append(('external/build_platform.txt',versionFileName, 'DATA'))
data_files.append(('logo_cineca.gif',os.path.join(ROOTPATH,'client','logo_cineca.gif'), 'DATA'))

print "------------->" , data_files
a = Analysis([    os.path.join(ROOTPATH,'client','rcm_client_tk.py')],
             pathex=[os.path.join(ROOTPATH,'server'), os.path.join(ROOTPATH,'Pyinstaller-2.1')])
#             hiddenimports=[],
#             hookspath=None)
pyz = PYZ(a.pure)

#remove from the binaries list all the X11 related dinamic libraries likelibX**

a.binaries=[x for x in a.binaries if not x[0].startswith("libX")]

print os.path.join(ROOTPATH, 'build','dist','Releases', outFile)

exe = EXE( pyz,
          a.scripts,
          a.binaries+ data_files,
          a.zipfiles,
          a.datas,
          #name=os.path.join(ROOTPATH, 'build','dist','Releases', outFile),
          name=os.path.join(outFile),
          debug=False,
          strip=False,
          upx=True,
          console=False )

build_collection_dir=False
if build_collection_dir:
	exe1 = EXE( pyz,
          a.scripts,
          name=os.path.join(outFile),
          debug=False,
          strip=False,
          upx=True,
          console=False,
          exclude_binaries=1 
        )

	dist = COLLECT( exe1,
          a.binaries+ data_files,
          a.zipfiles,
          a.datas,
          #name=os.path.join(ROOTPATH, 'build','dist','Releases', outFile),
          name=os.path.join(outFile+'_dir')
        )


fh = open(os.path.join(ROOTPATH, 'build','dist','Releases', outFile), 'rb')
m = hashlib.md5()
while True:
  data = fh.read(8192)
  if not data:
    break
  m.update(data)
currentChecksum = m.hexdigest()


rcmExe = os.path.join(ROOTPATH, 'build','dist','Releases', outFile)
zf=zipfile.ZipFile(rcmExe + ".zip" ,"w")
zf.write(rcmExe,outFile)
zf.close()


#write configuratin line
line = myplatform + " " + currentChecksum + " " + baseurl + os.path.basename(rcmExe) + '\n'
outFile = os.path.join(ROOTPATH,"build","dist", "checksum.txt")
with open(outFile, 'w') as outF:
    outF.write(myplatform+"\n")
    outF.write(currentChecksum+"\n")
    outF.write(os.path.basename(rcmExe)+"\n")
    outF.close()

exit()
#update versionRCM.cfg
configurationFile = os.path.join(ROOTPATH,"server", "versionRCM.cfg")
with open(configurationFile, 'r') as inF:
    fileContent = inF.readlines()
    inF.close()
    

checksumWritten = False
for idx, line in enumerate(fileContent):    
    if myplatform in line:
        if(checksumWritten == False):
            line = myplatform + " = " + currentChecksum + '\n'
            fileContent[idx] = line
            checksumWritten = True
        else:
            line = myplatform + " = " + baseurl + os.path.basename(rcmExe) + '\n'
            fileContent[idx] = line
            break
if not checksumWritten:
    with open(configurationFile, 'w') as outF:
        for idx, line in enumerate(fileContent):    
            if '[checksum]' in line:
                fileContent.insert(idx+1, myplatform + " = " + currentChecksum + '\n')
            if '[url]' in line:
                fileContent.insert(idx+1, myplatform + " = " + baseurl + os.path.basename(rcmExe) + '\n')

with open(configurationFile, 'w') as outF:
    for line in fileContent:
        outF.write(line)
outF.close()


print myplatform + ' = ' + currentChecksum

