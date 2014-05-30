#!/bin/bash


export BASE_DIR=`pwd`
export SRC_DIR=${BASE_DIR}/src
export INSTALL_DIR=${BASE_DIR}/install
export VENV_DIR=${BASE_DIR}/venv

mkdir -p $SRC_DIR
mkdir -p $INSTALL_DIR

export PATH=${INSTALL_DIR}/bin:${PATH}
export LD_LIBRARY_PATH=${INSTALL_DIR}/lib:${LD_LIBRARY_PATH}

cd $SRC_DIR
echo "Source dir ---> $SRC_DIR"
echo "Base dir ----> $BASE_DIR"


if [ -d ${SRC_DIR}/tcl8.5.15 ]; then
	echo "Skip ${SRC_DIR}/tcl8.5.15"
else
	#download tcl
	wget http://prdownloads.sourceforge.net/tcl/tcl8.5.15-src.tar.gz
	#unpack
	tar xvzf  tcl8.5.15-src.tar.gz
	#configure,make,install
	cd ${SRC_DIR}/tcl8.5.15/unix
	./configure --prefix=$INSTALL_DIR --exec-prefix=$INSTALL_DIR
	make 
	make install
fi

if [ -d ${SRC_DIR}/tk8.5.15 ]; then
	echo "Skip ${SRC_DIR}/tk8.5.15"
else
	#download tk
        cd ${SRC_DIR}
	wget http://prdownloads.sourceforge.net/tcl/tk8.5.15-src.tar.gz
	tar xvzf  tk8.5.15-src.tar.gz
	cd ${SRC_DIR}/tk8.5.15/unix
	./configure --prefix=$INSTALL_DIR --exec-prefix=$INSTALL_DIR --with-tcl=${SRC_DIR}/tcl8.5.15/unix
	make 
	make install
fi

if [ -d ${SRC_DIR}/Python-2.7.6 ]; then
	echo "Skip ${SRC_DIR}/Python-2.7.6"
else
        cd ${SRC_DIR}
        if [ -s ${SRC_DIR}/Python-2.7.6.tgz ]; then
	     echo "Skip download of ${SRC_DIR}/Python-2.7.6.tgz"
        else
	     #download python
	     wget --no-check-certificate http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz
        fi
	tar -xzf Python-2.7.6.tgz
	cd ${SRC_DIR}/Python-2.7.6
        ./configure --prefix=$INSTALL_DIR --exec-prefix=$INSTALL_DIR --with-tcltk-includes=${INSTALL_DIR}/include --with-tcltk-libs=${INSTALL_DIR}/lib
	make 
	make install
fi
#python -c "import Tkinter; a=Tkinter.Tk(); print 'fontsystem-->',a.call('::tk::pkgconfig','get','fontsystem'); import tkFont; print tkFont.families(); Tkinter._test()"

venv_cmd=`which virtualenv`
if [ "${INSTALL_DIR}/bin/virtualenv" == "${venv_cmd}" ]; then
	echo "skip virtualenv install"
else
	if [ -f ${SRC_DIR}/ez_setup.py ]; then
		echo "Skip ${SRC_DIR}/ez_setup.py"
	else
		cd ${SRC_DIR}
		wget http://peak.telecommunity.com/dist/ez_setup.py
	fi

	cd ${SRC_DIR}
	python ez_setup.py
	easy_install virtualenv
fi

if [ -d ${VENV_DIR} ]; then
	echo "skip virtualenv creation"
else
	virtualenv --system-site-packages ${VENV_DIR}	
        echo 'export LD_LIBRARY_PATH=${INSTALL_DIR}/lib:${LD_LIBRARY_PATH}' >> ${VENV_DIR}/bin/activate
fi

source ${VENV_DIR}/bin/activate
pip_cmd=`which pip`

if [ "${VENV_DIR}/bin/pip" == "${pip_cmd}" ]; then
	echo "pip command seems correct"
	pip install pycrypto
	pip install paramiko
	pip install pexpect
else
	echo "probably invalid pip command -->${pip_cmd}<--"
fi

