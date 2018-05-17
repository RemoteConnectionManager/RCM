# -*- mode: python -*-

block_cipher = None
import os
import sys
import platform
import shutil
basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

exe_name = 'RCM' + '_' + str(sys.platform) + '_' + str(platform.architecture()[0])
exe_path = os.path.join('dist', exe_name)

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

exe_sd = EXE(pyz,
             a.scripts,
             exclude_binaries=True,
             name=exe_name,
             debug=False,
             strip=False,
             upx=True,
             console=True)
coll = COLLECT(exe_sd,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=exe_name)

shutil.make_archive(exe_path, 'zip', exe_path)
shutil.rmtree(exe_path)

exe_se = EXE(pyz,
             a.scripts,
             a.binaries,
             a.zipfiles,
             a.datas,
             name=exe_name,
             debug=False,
             strip=False,
             upx=True,
             runtime_tmpdir=None,
             console=True)
