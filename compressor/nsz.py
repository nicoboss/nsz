#!/usr/bin/python3
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

#sys.path.insert(0, 'nut')

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

		parser.add_argument('-i', '--info', help='show info about title or file')
		parser.add_argument('--depth', type=int, default=1, help='max depth for file info and extraction')
		parser.add_argument('-N', '--verify-ncas', help='Verify NCAs in container')
		parser.add_argument('-x', '--extract', nargs='+', help='extract / unpack a NSP')
		parser.add_argument('-c', '--create', help='create / pack a NSP')
		parser.add_argument('-C', action="store_true", help='Compress NSP')
		parser.add_argument('-D', action="store_true", help='Decompress NSZ [Option currently disabled]')
		parser.add_argument('-l', '--level', type=int, default=17, help='Compression Level')
		parser.add_argument('-b', '--bs', type=int, default=19, help='Block Size for random read access 2^x while x between 14 and 32.  Current title installers do not support this yet')
		parser.add_argument('-s', '--solid', type=bool, default=True, help='Uses solid instead of block compression. Slightly better compression ratio but no random read access support')
		parser.add_argument('-o', '--output', help='Directory to save the output NSZ files')
		parser.add_argument('-t', '--threads', type=int, default=0, help='[Option currently disabled] Number of threads to compress with.  Negative corresponds to the number of logical CPU cores.')

		
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
							nut.compress(filePath, 17 if args.level is None else args.level, args.solid, args.bs, args.output, args.threads)

					except BaseException as e:
						Print.error(str(e))
						raise
						
		if args.D:
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsz'):
							print("Decompress NSZ is currently disabled")
							#nut.decompress(filePath, args.output)

					except BaseException as e:
						Print.error(str(e))
						raise
		
		if args.info:
			f = Fs.factory(args.info)
			f.open(args.info, 'r+b')

			f.printInfo(args.depth+1)

		if args.verify_ncas:
			nut.initTitles()
			nut.initFiles()
			f = Fs.factory(args.verify_ncas)
			f.open(args.verify_ncas, 'r+b')
			if not f.verify():
				Print.error('Archive is INVALID: %s' % args.verify_ncas)
			else:
				Print.error('Archive is VALID: %s' % args.verify_ncas)
			f.close()

			if not Titles.contains(args.scrape_title):
				Print.error('Could not find title ' + args.scrape_title)
			else:
				Titles.get(args.scrape_title).scrape(False)
				Titles.save()
				pprint.pprint(Titles.get(args.scrape_title).__dict__)


		
		if len(sys.argv)==1:
			pass

	except KeyboardInterrupt:
		Print.info('Keyboard exception')
	except BaseException as e:
		Print.info('nut exception: ' + str(e))
		raise

	Print.info('fin')

