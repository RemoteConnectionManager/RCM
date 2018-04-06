# RCM
RCM is a VNC client for the remote visualization on the CINECA clusters.

## Setup
```sh
mkdir <new_folder>
cd <new_folder>
git clone git clone https://github.com/RemoteConnectionManager/rcm-client.git
sudo apt-get install virtualenv -y
virtualenv -p python3 py3env
source py3env/bin/activate
cd rcm-client
pip3 install -r requirements.txt
```

