# RCM
RCM is a VNC client for the remote visualization on the CINECA clusters.

## Setup

### Linux Setup
```sh
mkdir <new_folder>
cd <new_folder>
git clone git clone https://github.com/RemoteConnectionManager/RCM.git
sudo apt-get install virtualenv -y
virtualenv -p python3 py3env
source py3env/bin/activate
pip3 install -r RCM/rcm/client/requirements.txt
```

### Run
```sh
source py3env/bin/activate
python RCM/rcm/client/rcm_client_qt.py
```

### Linux dist build
```sh
source py3env/bin/activate
cd RCM/rcm/client
pyinstaller rcm_client_qt.spec
```
