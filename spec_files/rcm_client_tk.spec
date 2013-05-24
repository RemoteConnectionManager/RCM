# -*- mode: python -*-
import platform
import hashlib
import subprocess

rcmVersion = "1.1."
customPlatform=''
baseurl="https://hpc-forge.cineca.it/svn/RemoteGraph/trunk/build/dist/Releases/"
    

ROOTPATH=os.path.dirname(os.path.dirname(os.path.abspath(HOMEPATH)))
print "---------------->", os.path.abspath(HOMEPATH)
print "---------------->",ROOTPATH

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
             pathex=[os.path.join(ROOTPATH,'server'), os.path.join(ROOTPATH,'pyinstaller-2.0')])
#             hiddenimports=[],
#             hookspath=None)
pyz = PYZ(a.pure)


exe = EXE( pyz,
          a.scripts,
          a.binaries+ data_files,
          a.zipfiles,
          a.datas,
          name=os.path.join(ROOTPATH, 'build','dist','Releases', outFile),
          debug=False,
          strip=False,
          upx=True,
          console=False )

fh = open(os.path.join(ROOTPATH, 'build','dist','Releases', outFile), 'rb')
m = hashlib.md5()
while True:
  data = fh.read(8192)
  if not data:
    break
  m.update(data)
currentChecksum = m.hexdigest()

#update versionRCM.cfg
configurationFile = os.path.join(ROOTPATH,"server", "versionRCM.cfg")
with open(configurationFile, 'r') as inF:
    fileContent = inF.readlines()
    inF.close()
    
rcmExe = os.path.join(ROOTPATH, 'build','dist','Releases', outFile)
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

