# -*- mode: python -*-

block_cipher = None
import os
import sys
basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

# pathex=['/home/sbna/Software/Devel/rcm/RCM/rcm/client'],

a = Analysis(['rcm_client_qt.py'],
             pathex=[(os.path.join(basepath, 'rcm/server'))],
             binaries=[],
             datas=[(os.path.join(basepath, 'rcm/client/gui/icons/*.png'), 'gui/icons/'),
                    (os.path.join(basepath, 'rcm/client/external/turbovnc'), 'turbovnc')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='rcm_client_qt',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )


