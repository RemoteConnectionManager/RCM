# -*- mode: python -*-
import platform
ROOTPATH=os.path.dirname(os.path.dirname(os.path.abspath(HOMEPATH)))
print "---------------->", os.path.abspath(HOMEPATH)
print "---------------->",ROOTPATH
if(sys.platform == 'win32'):
  data_files=[('external/win32/32bit/bin/vncviewer.exe', os.path.join(ROOTPATH,'client','external','win32','32bit','bin','vncviewer.exe'), 'DATA'),('external/win32/32bit/bin/PLINK.EXE', os.path.join(ROOTPATH,'client','external','win32','32bit','bin','PLINK.EXE'), 'DATA')]
  outFile = 'RCM.exe'
else:
  myplatform=platform.architecture()[0]
  print "----",platform
  data_files=[('external/'+sys.platform+'/'+myplatform+'/bin/vncviewer', os.path.join(ROOTPATH,'client','external',sys.platform,myplatform,'bin','vncviewer'), 'DATA')]
  outFile = 'RCM'
  if sys.platform.startswith('linux'):
    outFile += '_' + platform.linux_distribution()[0] + '_' + platform.linux_distribution()[1]
a = Analysis([os.path.join(HOMEPATH,'support','_mountzlib.py'), os.path.join(HOMEPATH,'support','unpackTK.py'), os.path.join(HOMEPATH,'support','useTK.py'), os.path.join(HOMEPATH,'support','useUnicode.py'), os.path.join(ROOTPATH,'client','crv_client_tk.py'), os.path.join(HOMEPATH,'support','removeTK.py')],
             pathex=[os.path.join(ROOTPATH,'python'), os.path.join(ROOTPATH,'pyinstaller-1.5.1')])
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
          console=True )
