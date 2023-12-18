import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name='nsz',
	version='4.6.1',
	script="nsz.py",
	author="Nico Bosshard",
	author_email="nico@bosshome.ch",
	maintainer="Nico Bosshard",
	maintainer_email="nico@bosshome.ch",
	description="NSZ - Homebrew compatible NSP/XCI compressor/decompressor",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/nicoboss/nsz",
	packages=['nsz', 'nsz.Fs', 'nsz.nut', 'nsz.gui', 'nsz.gui.txt', 'nsz.gui.shaders', 'nsz.gui.layout', 'nsz.gui.json', 'nsz.gui.fonts'],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	install_requires=[
		'pycryptodome',
		'zstandard',
		'enlighten',
	],
	extras_require={
		'gui': [
			'pywin32;platform_system=="Windows"',
			'pypiwin32;platform_system=="Windows"',
			'kivy'
		]
	},
	entry_points = {'console_scripts': ['nsz = nsz:main']},
	keywords = ['nsz', 'xcz', 'ncz', 'nsp', 'xci', 'nca', 'Switch'],
	python_requires='>=3.6',
	zip_safe=False,
	include_package_data=True,
 )
