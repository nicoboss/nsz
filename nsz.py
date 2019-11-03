#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import re
import pathlib
import json
import traceback

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
from nsz import FileExistingChecks
import glob

# I think we should definitely change the code below.
# If nsz.py executed like this:
# python /path/to/nsz/nsz.py -C -o /path/to/out file.nsp
# This causes nsz.py to search the file in /path/to/nsz directory.
# It should return ./file.nsp or /path/to/nsp/file.nsp
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
	
err = []

if __name__ == '__main__':
	try:

		#signal.signal(signal.SIGINT, handler)


		parser = argparse.ArgumentParser()
		parser.add_argument('file',nargs='*')

		parser.add_argument('-C', action="store_true", help='Compress NSP')
		parser.add_argument('-D', action="store_true", help='Decompress NSZ')
		parser.add_argument('-l', '--level', type=int, default=18, help='Compression Level')
		parser.add_argument('-B', '--block', action="store_true", default=False, help='Uses highly multithreaded block compression with random read access allowing compressed games to be played without decompression in the future however this comes with a low compression ratio cost. Current title installers do not support this yet.')
		parser.add_argument('-s', '--bs', type=int, default=20, help='Block Size for random read access 2^x while x between 14 and 32. Default is 20 => 1 MB. Current title installers do not support this yet.')
		parser.add_argument('-V', '--verify', action="store_true", default=False, help='Verifies files after compression raising an unhandled exception on hash mismatch and verify existing NSP and NSZ files when given as parameter')
		parser.add_argument('-t', '--threads', type=int, default=-1, help='Number of threads to compress with. Numbers < 1 corresponds to the number of logical CPU cores.')
		parser.add_argument('-o', '--output', default="", help='Directory to save the output NSZ files')
		parser.add_argument('-w', '--overwrite', action="store_true", default=False, help='Continues even if there already is a file with the same name or title id inside the output directory')
		parser.add_argument('-r', '--rm-old-version', action="store_true", default=False, help='Removes older version if found')
		parser.add_argument('-i', '--info', help='Show info about title or file')
		parser.add_argument('--depth', type=int, default=1, help='Max depth for file info and extraction')
		parser.add_argument('-x', '--extract', nargs='+', help='extract / unpack a NSP')
		parser.add_argument('-c', '--create', help='create / pack a NSP')
		parser.add_argument('--rm-source', action='store_true', default=False, help='Deletes source file/s after compressing/decompressing. It\'s recommended to only use this in combination with --verify')

		
		args = parser.parse_args()
		outfolder = args.output if args.output else os.path.join(os.path.abspath('.'))

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
			targetDict = FileExistingChecks.CreateTargetDict(outfolder, ".nsz")
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsp'):
							if not FileExistingChecks.AllowedToWriteOutfile(filePath, ".nsz", targetDict, args.rm_old_version, args.overwrite):
								continue
							nsz.compress(filePath, args)

							if args.rm_source:
								FileExistingChecks.delete_source_file(filePath)

					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when compressing file: %s' % filePath)
						err.append({"filename":filePath,"error":traceback.format_exc() })
						traceback.print_exc()
						#raise
						
		if args.D:
			targetDict = FileExistingChecks.CreateTargetDict(outfolder, ".nsp")
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsz'):
							if not FileExistingChecks.AllowedToWriteOutfile(filePath, ".nsp", targetDict, args.rm_old_version, args.overwrite):
								continue
							nsz.decompress(filePath, args.output)
							if args.rm_source:
								FileExistingChecks.delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when decompressing file: %s' % filePath)
						err.append({"filename":filePath,"error":traceback.format_exc() })
						traceback.print_exc()
						#raise
		
		if args.info:
			f = Fs.factory(args.info)
			f.open(args.info, 'r+b')

			f.printInfo(args.depth+1)

		if args.verify and not args.C and not args.D:
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsp') or filePath.endswith('.nsz'):
							if filePath.endswith('.nsp'):
								print("[VERIFY NSP] {0}".format(i))
							if filePath.endswith('.nsz'):
								print("[VERIFY NSZ] {0}".format(i))
							nsz.verify(filePath, False)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when verifying file: %s' % filePath)
						err.append({"filename":filePath,"error":traceback.format_exc() })
						traceback.print_exc()
						#raise
		
		
		if len(sys.argv) == 1:
			pass

	except KeyboardInterrupt:
		Print.info('Keyboard exception')
	except BaseException as e:
		Print.info('nut exception: ' + str(e))
		raise
	if err:
		Print.info('\033[93m\033[1mErrors:')
		for e in err:
			Print.info('\033[0mError when processing %s' % e["filename"] )
			Print.info(e["error"])
			

	Print.info('fin')

