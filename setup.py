import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name='nsz',
	version='2.1.1',
	script="nsz.py",
	author="Nico Bosshard",
	author_email="nico@bosshome.ch",
	maintainer="Nico Bosshard",
	maintainer_email="nico@bosshome.ch",
	description="NSZ - Homebrew compatible NSP/XCI compressor/decompressor",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/nicoboss/nsz",
	packages=['nsz', 'nsz/Fs', 'nsz/nut'],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	install_requires=['pycryptodome>=3.9.0', 'zstandard', 'colorama', 'tqdm', 'kivy_deps.sdl2==0.1.22', 'kivy_deps.glew==0.1.12', 'kivy==1.11.1'],
	entry_points = {'console_scripts': ['nsz = nsz:main']},
	keywords = ['nsz', 'xcz', 'ncz', 'nsp', 'xci'],
	python_requires='>=3.6',
	zip_safe=False,
 )
