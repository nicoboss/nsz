#!/bin/bash
if [[ `id -u` != 0 ]]; then
    echo "This script must be run as root."
    exit
fi

if [ -n "`which apt`" ]
then
	apt install -y \
		build-essential \
		git \
		python3 \
		python3-dev \
		python3-pip \
		ffmpeg \
		libsdl2-dev \
		libsdl2-image-dev \
		libsdl2-mixer-dev \
		libsdl2-ttf-dev \
		libportmidi-dev \
		libswscale-dev \
		libavformat-dev \
		libavcodec-dev \
		zlib1g-dev
	apt remove -y cython3
	# Install gstreamer for audio, video (optional)
	apt install -y \
		libgstreamer1.0 \
		gstreamer1.0-plugins-base \
		gstreamer1.0-plugins-good
elif [ -n "`which dnf`" ]
then
	#Add required repositories
	if [ ! $(rpm -E %fedora) = "%fedora" ]
	then
		dnf install -y --nogpgcheck https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
	fi
	
	if [ ! $(rpm -E %rhel) = "%rhel" ]
	then
		dnf install -y --nogpgcheck https://download1.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm
		dnf install -y dnf-plugins-core
		dnf config-manager --enable PowerTools
		dnf update
	fi
	dnf -y upgrade
	
	dnf -y groupinstall "Development Tools"
	
	# Install necessary system packages
	dnf install -y git
	dnf install -y python3-devel
	dnf install -y ffmpeg-libs
	dnf install -y SDL2-devel
	dnf install -y SDL2_image-devel
	dnf install -y SDL2_mixer-devel
	dnf install -y SDL2_ttf-devel
	dnf install -y portmidi-devel
	dnf install -y libavdevice
	dnf install -y libavc1394-devel
	dnf install -y zlibrary-devel
	dnf install -y ccache mesa-libGL
	dnf install -y mesa-libGL-devel
	dnf install -y libXrandr-devel
	
	# Install xclip in case you run a kivy app using your computer, and the app requires a CutBuffer provider:
	dnf install -y xclip
	
	# avoid pip Cython conflict with packaged version:
	dnf remove python3-Cython
fi

# make sure pip and setuptools are updated
python3 -m pip install --upgrade --user pip setuptools

# if you'd like to be able to use the x11 winodw backend do:
export USE_X11=1

#Building Kivy from source
python3 -m pip install pygments docutils pillow
python3 -m pip install --upgrade "Cython>=0.24,<=0.29.14,!=0.27,!=0.27.2"
rm -rf kivy
git clone git://github.com/kivy/kivy.git
cd kivy
sed -i 's/PYTHON = python/PYTHON = python3/g' Makefile
python3 setup.py build_ext --inplace -f
pip3 install .
cd ..
rm -rf kivy
pip3 install .

#Installing NSZ dependencies
python3 -m pip install pycryptodome>=3.9.0
python3 -m pip install zstandard
python3 -m pip install enlighten
