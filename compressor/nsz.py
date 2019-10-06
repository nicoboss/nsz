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
		parser.add_argument('-l', '--level', type=int, default=17, help='Compression Level')
		parser.add_argument('-o', '--output', help='Directory to save the output NSZ files')

		
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
			for filePath in args.file:
				try:
					nut.compress(filePath, 17 if args.level is None else args.level, args.output)

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

