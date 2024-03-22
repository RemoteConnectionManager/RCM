from hatchling.builders.hooks.plugin.interface import BuildHookInterface


import subprocess
from sys import platform
import urllib.request
import tarfile
import zipfile
import shutil
import os
import re
import pathlib
from distutils.dir_util import copy_tree

TURBOVNC_VERSION = "3.1.1"
STEP_VERSION = "0.25.2"
RCM_CLIENT_EXTERNAL = "rcm/client/external"


def clean_mkdir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok = True)


def external_turbovnc():
    turbovnc_preurl = "https://github.com/TurboVNC/turbovnc/releases/download"
    turbovnc_taget_dir = f"{RCM_CLIENT_EXTERNAL}/turbovnc"
    orig_line = r'^jdk.tls.disabledAlgorithms=SSLv3, TLSv1, TLSv1.1, RC4, DES, MD5withRSA,'
    new_line = 'jdk.tls.disabledAlgorithms=SSLv3, RC4, DES, MD5withRSA,'

    if platform.startswith("linux"):
        clean_mkdir("tmp")

        # Download turbovnc
        turbovnc_url = "{0}/{1}/turbovnc_{1}_amd64.deb".format(turbovnc_preurl, TURBOVNC_VERSION)
        urllib.request.urlretrieve(turbovnc_url, "tmp/turbovnc.deb")

        # Extract turbovnc
        subprocess.run(["dpkg-deb", "-x", "tmp/turbovnc.deb", "tmp/turbovnc"])

        clean_mkdir(turbovnc_taget_dir)

        for i in ["opt/TurboVNC", "usr/share"]:
            copy_tree(f"tmp/turbovnc/{i}", turbovnc_taget_dir)

        shutil.rmtree("tmp")

    elif platform == "win32":
        clean_mkdir("tmp")
        urllib.request.urlretrieve("https://github.com/dscharrer/innoextract/releases/download/1.9/innoextract-1.9-windows.zip", "tmp/innoextract.zip")

        with zipfile.ZipFile('tmp/innoextract.zip') as z:
            with open('tmp/innoextract.exe', 'wb') as target:
                target.write(z.read(f'innoextract.exe'))

        # Download turbovnc
        turbovnc_url = "{0}/{1}/TurboVNC-{1}-x64.exe".format(turbovnc_preurl, TURBOVNC_VERSION)
        urllib.request.urlretrieve(turbovnc_url, "tmp/turbovnc.exe")

        # Extract turbovnc
        os.chdir('tmp')
        subprocess.run(['innoextract.exe', 'turbovnc.exe'])
        os.chdir('..')

        clean_mkdir(f"{turbovnc_taget_dir}")
        shutil.copytree("tmp/app", f"{turbovnc_taget_dir}/bin")

        shutil.rmtree("tmp")

    elif platform == "darwin":
        pass

    if platform.startswith('linux') or platform == 'win32':
        java_security = list(pathlib.Path(turbovnc_taget_dir).glob('**/java.security'))[0]
        with open(java_security, "r") as sources:
            lines = sources.readlines()
        with open(java_security, "w") as sources:
            for line in lines:
                sources.write(re.sub(orig_line, new_line, line))


def external_step():
    step_preurl = "https://github.com/smallstep/cli/releases/download"
    step_taget_dir = f"{RCM_CLIENT_EXTERNAL}/step"

    if platform.startswith("linux"):
        clean_mkdir("tmp")
        step_url = "{0}/v{1}/step_linux_{1}_amd64.tar.gz".format(step_preurl, STEP_VERSION)
        urllib.request.urlretrieve(step_url, "tmp/step.tgz")

        with tarfile.open("tmp/step.tgz", 'r:gz') as tgz:
            tgz.extract(f"step_{STEP_VERSION}/bin/step", 'tmp')
        
        clean_mkdir(step_taget_dir)
        shutil.copy(f"tmp/step_{STEP_VERSION}/bin/step", step_taget_dir)

        shutil.rmtree("tmp")

    elif platform == "win32":
        clean_mkdir("tmp")
        step_url = "{0}/v{1}/step_windows_{1}_amd64.zip".format(step_preurl, STEP_VERSION)
        urllib.request.urlretrieve(step_url, "tmp/step.zip")

        clean_mkdir(step_taget_dir)

        with zipfile.ZipFile('tmp/step.zip') as z:
            with open(f'{step_taget_dir}/step.exe', 'wb') as target:
                target.write(z.read(f'step_{STEP_VERSION}/bin/step.exe'))

        shutil.rmtree("tmp")

    elif platform == "darwin":
        pass


class ExternalBuildHook(BuildHookInterface):
    PLUGIN_NAME = "external"

    def initialize(self, _version, build_data):
        # _version='standard'
        # _build_data={'infer_tag': False, 'pure_python': True, 'dependencies': [], 'force_include_editable': {}, 'extra_metadata': {}, 'artifacts': [], 'force_include': {}, 'build_hooks': ('custom',)}
        external_turbovnc()
        external_step()
        build_data['infer_tag'] = True
        build_data['pure_python'] = False
        # build_data['artifacts'].extend(self.artifact_patterns)
        # build_data['force_include'].update(self.get_forced_inclusion_map())