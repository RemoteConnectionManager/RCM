# -*- mode: python -*-

block_cipher = None
import os
import sys
import platform
import shutil
basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

version = "1.0"
distribution_name = ''
if len(sys.argv) > 2:
    version = str(sys.argv[2])
    print("RCM version: " + version)
if len(sys.argv) > 3:
    distribution_name = str(sys.argv[3]).split('/')[0]
    print("RCM distribution: " + distribution_name)
# this, should extract the part of the version name that comes after '_' or ''
# has to be applied to the output of git describe --tags --long
# like "v0.0.8-132-gdb62f50" --> ''
# "v0.0.8_dev-132-gdb62f50" --> 'dev'
platform_version = (version.strip().rsplit("-")[0].split("_")[1:][-1:]+[""])[0]
platform = str(sys.platform) + '_' + str(platform.architecture()[0]) + '_' + distribution_name + '_' + platform_version
exe_name = 'RCM' + platform_version
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
             console=False)
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
             console=False)


workdir = os.path.abspath(os.path.join('dist', platform, version))
if not os.path.exists(workdir):
    os.makedirs(workdir)
if sys.platform == 'win32':
    exe_extension = '.exe'
else:
    exe_extension = ''
for filename in [exe_name + exe_extension, exe_name + '.zip']:
    shutil.move(os.path.join('dist', filename), os.path.join(workdir, filename))
