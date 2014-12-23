cd /home/vagrant/devel/RCM/build_env
wget http://sourceforge.net/projects/turbovnc/files/1.2.2/turbovnc_1.2.2_amd64.deb
mkdir turbovnc_1.2.2_amd64
dpkg -x turbovnc_1.2.2_amd64.deb turbovnc_1.2.2_amd64
cd turbovnc_1.2.2_amd64
cp opt/TurboVNC/bin/vncviewer /home/vagrant/devel/RCM/multivnc/client/external/linux2/64bit/bin/vncviewer
