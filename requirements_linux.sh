if [ -n "`which apt-get`" ]
	then apt-get -y install libgl-dev
elif [ -n "`which yum`" ]
	then yum -y install mesa-libGL-devel
fi
pip3 install kivy==1.11.1
pip3 install pygame
pip3 install pycryptodome>=3.9.0
pip3 install zstandard
pip3 install enlighten
