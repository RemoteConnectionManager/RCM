# -*- mode: python -*-

block_cipher = None
import os
import sys
import platform
import shutil
basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

version = "1.0"
if len(sys.argv) > 2:
    version = str(sys.argv[2])
    print("RCM version: " + version)
# this, should extract the part of the version name that comes after '_' or ''
# has to be applied to the output of git describe --tags --long
# like "v0.0.8-132-gdb62f50" --> ''
# "v0.0.8_dev-132-gdb62f50" --> 'dev'
platform_version = (version.strip().rsplit("-")[0].split("_")[1:][-1:]+[""])[0]
platform = str(sys.platform) + '_' + str(platform.architecture()[0]) + platform_version
exe_name = 'RCM' + '_' + platform
exe_path = os.path.join('dist', exe_name)

build_platform_filename = os.path.join(basepath, 'build_platform.txt')
with open(build_platform_filename, "w") as f:
    f.write(platform + '\n')
    f.write(version)

a = Analysis(['rcm_client_qt.py'],
             pathex=[(os.path.join(basepath, 'rcm/server'))],
             binaries=[],
             datas=[(os.path.join(basepath, 'rcm/client/gui/icons/*.png'), 'gui/icons/'),
                    (os.path.join(basepath, 'rcm/client/external/turbovnc'), 'turbovnc'),
                    (os.path.join(basepath, 'build_platform.txt'), '')],
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
