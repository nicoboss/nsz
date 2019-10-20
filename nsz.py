#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import re
import pathlib
import urllib3
import json

if not getattr(sys, 'frozen', False):
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

import Fs
import Fs.Nsp
from nut import Hex
from nut import Print
import time
import colorama
import pprint
import random
import queue
import nut
import nsz

def expandFiles(path):
	files = []
	path = os.path.abspath(path)

	if os.path.isfile(path):
		files.append(path)
	else:
		for f in os.listdir(path):
			f = os.path.join(path, f)
			if os.path.isfile(f) and (f.endswith('.nsp') or f.endswith('.nsz')):
				files.append(f)
	return files
	


if __name__ == '__main__':
	try:
		urllib3.disable_warnings()

		#signal.signal(signal.SIGINT, handler)


		parser = argparse.ArgumentParser()
		parser.add_argument('file',nargs='*')

		parser.add_argument('-C', action="store_true", help='Compress NSP')
		parser.add_argument('-D', action="store_true", help='Decompress NSZ')
		parser.add_argument('-l', '--level', type=int, default=18, help='Compression Level')
		parser.add_argument('-B', '--block', action="store_true", default=False, help='Uses highly multithreaded block compression with random read access allowing compressed games to be played without decompression in the future however this comes with a low compression ratio cost. Current title installers do not support this yet.')
		parser.add_argument('-s', '--bs', type=int, default=20, help='Block Size for random read access 2^x while x between 14 and 32. Default is 20 => 1 MB. Current title installers do not support this yet.')
		parser.add_argument('-t', '--threads', type=int, default=-1, help='Number of threads to compress with. Usless without enabeling block compression using -B. Numbers < 1 corresponds to the number of logical CPU cores.')
		parser.add_argument('-o', '--output', help='Directory to save the output NSZ files')
		parser.add_argument('-w', '--overwrite', action="store_true", default=False, help='Continues even if there already is a file with the same name or title id inside the output directory')
		parser.add_argument('-i', '--info', help='Show info about title or file')
		parser.add_argument('--depth', type=int, default=1, help='Max depth for file info and extraction')
		parser.add_argument('-x', '--extract', nargs='+', help='extract / unpack a NSP')
		parser.add_argument('-c', '--create', help='create / pack a NSP')
		parser.add_argument('-V', '--verify', action="store_true", default=False, help='Verify existing NSP and NSZ files')
		

		
		args = parser.parse_args()


		Print.info('                        ,;:;;,')
		Print.info('                       ;;;;;')
		Print.info('               .=\',    ;:;;:,')
		Print.info('              /_\', "=. \';:;:;')
		Print.info('              @=:__,  \,;:;:\'')
		Print.info('                _(\.=  ;:;;\'')
		Print.info('               `"_(  _/="`')
		Print.info('                `"\'')

		if args.extract:
			for filePath in args.extract:
				f = Fs.factory(filePath)
				f.open(filePath, 'rb')
				dir = os.path.splitext(os.path.basename(filePath))[0]
				f.unpack(dir)
				f.close()

		if args.create:
			Print.info('creating ' + args.create)
			nsp = Fs.Nsp.Nsp(None, None)
			nsp.path = args.create
			nsp.pack(args.file)
		
		if args.C:
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsp'):
							nsz.compress(filePath, 18 if args.level is None else args.level, args.block, args.bs, args.output, args.threads, args.overwrite)
					except BaseException as e:
						Print.error(str(e))
						raise
						
		if args.D:
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsz'):
							nsz.decompress(filePath, args.output)
					except BaseException as e:
						Print.error(str(e))
						raise
		
		if args.info:
			f = Fs.factory(args.info)
			f.open(args.info, 'r+b')

			f.printInfo(args.depth+1)

		if args.verify:
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsp') or filePath.endswith('.nsz'):
							if filePath.endswith('.nsp'):
								print("[VERIFY NSP] {0}".format(i))
							if filePath.endswith('.nsz'):
								print("[VERIFY NSZ] {0}".format(i))
							nsz.verify(filePath)
					except BaseException as e:
						Print.error(str(e))
						raise


		
		if len(sys.argv)==1:
			pass

	except KeyboardInterrupt:
		Print.info('Keyboard exception')
	except BaseException as e:
		Print.info('nut exception: ' + str(e))
		raise

	Print.info('fin')

