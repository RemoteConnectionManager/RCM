# rcm-client
rcm-client is a VNC client for the remote visualization on the CINECA clusters.

## Setup

### Linux 

#### Setup

For the turbovnc installation, read [here](https://github.com/RemoteConnectionManager/RCM_spack_deploy/tree/dev/recipes/hosts/ws_mint).
For the python-qt part, instructions are below:

```sh
mkdir <new_folder>
cd <new_folder>
git clone https://github.com/RemoteConnectionManager/RCM.git
sudo apt-get install virtualenv -y
virtualenv -p python3 py3env
source py3env/bin/activate
pip3 install -r RCM/rcm/client/requirements.txt
```

#### Run
```sh
source py3env/bin/activate
source <rcm_spack_deploy_dir>/deploy/rcm_client/dev/spack/share/spack/setup-env.sh
module load turbovnc
python RCM/rcm/client/rcm_client_qt.py
```

#### Dist build
In order to create the distribution, you need to install in the turbovnc folder at the same level of RCM
the vncviewer with its dependecies.

```sh
source py3env/bin/activate
cd RCM/rcm/client
pyinstaller rcm_client_qt_onedir.spec
```

### Windows

#### Setup

Download and install Python3.5 or higher with pip3 (https://www.python.org/downloads/).
Clone the repository with a git client. Then install the virtualenv package,
create a new virtual environment, activate it and install there the dependencies. 

```sh
pip3.exe install virtualenv
cd <base_dir>
<python_install_dir>\Scripts\virtualenv py3env
py3env\Scripts\activate
pip3 install -r RCM\rcm\client\requirements.txt
```
