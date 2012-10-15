# -*- mode: python -*-
import platform
import hashlib
import subprocess

rcmVersion = "1.0."

ROOTPATH=os.path.dirname(os.path.dirname(os.path.abspath(HOMEPATH)))
print "---------------->", os.path.abspath(HOMEPATH)
print "---------------->",ROOTPATH

#add revision to rcm version 
myprocess = subprocess.Popen(["svnversion",ROOTPATH],stdout=subprocess.PIPE)
(myout,myerr)=myprocess.communicate()

print "revision number:" + str(myout)
rcmVersion = rcmVersion + str(myout)
rcmVersion = rcmVersion.rstrip()

myplatform=sys.platform + '_' + platform.architecture()[0]

outFile = 'RCM_'
if(sys.platform == 'win32'):
  data_files=[('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/vncviewer.exe', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','vncviewer.exe'), 'DATA'),('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/PLINK.EXE', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','PLINK.EXE'), 'DATA')]
  outFile += myplatform +'.exe'
else:
  data_files=[('external/'+sys.platform+'/'+platform.architecture()[0]+'/bin/vncviewer', os.path.join(ROOTPATH,'client','external',sys.platform,platform.architecture()[0],'bin','vncviewer'), 'DATA')]
  if sys.platform.startswith('linux'):
    myplatform += '_' + platform.linux_distribution()[0] + '_' + platform.linux_distribution()[1]
  outFile += myplatform
print "Building ----> ",outFile

print "------------->" , data_files

versionFileName = os.path.join(ROOTPATH, 'build','dist', 'build_platform.txt')
versionfile = open(versionFileName,"w")
versionfile.write(myplatform + '\n')
versionfile.write(rcmVersion)
versionfile.close()
data_files.append(('external/build_platform.txt',versionFileName, 'DATA'))

print "------------->" , data_files
a = Analysis([os.path.join(HOMEPATH,'support','_mountzlib.py'), os.path.join(HOMEPATH,'support','unpackTK.py'), os.path.join(HOMEPATH,'support','useTK.py'), os.path.join(HOMEPATH,'support','useUnicode.py'), os.path.join(ROOTPATH,'client','rcm_client_tk.py'), os.path.join(HOMEPATH,'support','removeTK.py')],
             pathex=[os.path.join(ROOTPATH,'server'), os.path.join(ROOTPATH,'pyinstaller-1.5.1')])
pyz = PYZ(a.pure)


exe = EXE(TkPKG(), pyz,
          a.scripts,
          a.binaries+ data_files,
          a.zipfiles,
          a.datas,
          name=os.path.join(ROOTPATH, 'build','dist', outFile),
          debug=False,
          strip=False,
          upx=True,
          console=False )

fh = open(os.path.join(ROOTPATH, 'build','dist', outFile), 'rb')
m = hashlib.md5()
while True:
  data = fh.read(8192)
  if not data:
    break
  m.update(data)
currentChecksum = m.hexdigest()
print myplatform + ' = ' + currentChecksum
