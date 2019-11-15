#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import path
from pathlib import Path
scriptPath = str(Path(__file__).resolve())
importPath = str(Path(scriptPath).parent)
path.append(importPath)

from sys import argv
from nut import Print
from os import listdir
from Fs import Nsp, factory
from argparse import ArgumentParser
from BlockCompressor import blockCompress
from SolidCompressor import solidCompress
from traceback import print_exc, format_exc
from NszDecompressor import verify as NszVerify, decompress as NszDecompress
from multiprocessing import cpu_count, freeze_support
from FileExistingChecks import CreateTargetDict, AllowedToWriteOutfile, delete_source_file

def compress(filePath, args):
	compressionLevel = 18 if args.level is None else args.level
	threadsToUse = args.threads if args.threads > 0 else cpu_count()
	if args.block:
		outFile = blockCompress(filePath, compressionLevel, args.bs, args.output, threadsToUse)
	else:
		if args.threads < 0:
			threadsToUse = 1
		outFile = solidCompress(filePath, compressionLevel, args.output, threadsToUse)
	if args.verify:
		print("[VERIFY NSZ] {0}".format(outFile))
		verify(outFile, True)

def decompress(filePath, outputDir = None):
	NszDecompress(filePath, outputDir)

def verify(filePath, raiseVerificationException):
	NszVerify(filePath, raiseVerificationException)

def expandFiles(path):
	files = []
	path = str(Path(path).resolve())

	if Path(path).is_file():
		files.append(path)
	else:
		for f in listdir(path):
			f = str(Path(path).joinpath(f))
			if Path(f).is_file() and (f.endswith('.nsp') or f.endswith('.nsz')):
				files.append(f)
	return files

err = []

def main():
	global err
	try:
		parser = ArgumentParser()
		parser.add_argument('file',nargs='*')
		parser.add_argument('-C', action="store_true", help='Compress NSP')
		parser.add_argument('-D', action="store_true", help='Decompress NSZ')
		parser.add_argument('-l', '--level', type=int, default=18, help='Compression Level')
		parser.add_argument('-B', '--block', action="store_true", default=False, help='Uses highly multithreaded block compression with random read access allowing compressed games to be played without decompression in the future however this comes with a low compression ratio cost. Current title installers do not support this yet.')
		parser.add_argument('-s', '--bs', type=int, default=20, help='Block Size for random read access 2^x while x between 14 and 32. Default is 20 => 1 MB. Current title installers do not support this yet.')
		parser.add_argument('-V', '--verify', action="store_true", default=False, help='Verifies files after compression raising an unhandled exception on hash mismatch and verify existing NSP and NSZ files when given as parameter')
		parser.add_argument('-p', '--parseCnmt', action="store_true", default=False, help='Extract TitleId/Version from Cnmt if this information cannot be obtained from the filename. Required for skipping/overwriting existing files and --rm-old-version to work properly if some not every file is named properly. Supported filenames: *TitleID*[vVersion]*')
		parser.add_argument('-t', '--threads', type=int, default=-1, help='Number of threads to compress with. Numbers < 1 corresponds to the number of logical CPU cores.')
		parser.add_argument('-o', '--output', nargs='?', help='Directory to save the output NSZ files')
		parser.add_argument('-w', '--overwrite', action="store_true", default=False, help='Continues even if there already is a file with the same name or title id inside the output directory')
		parser.add_argument('-r', '--rm-old-version', action="store_true", default=False, help='Removes older version if found')
		parser.add_argument('-i', '--info', help='Show info about title or file')
		parser.add_argument('--depth', type=int, default=1, help='Max depth for file info and extraction')
		parser.add_argument('-x', '--extract', nargs='+', help='extract / unpack a NSP')
		parser.add_argument('-c', '--create', help='create / pack a NSP')
		parser.add_argument('--rm-source', action='store_true', default=False, help='Deletes source file/s after compressing/decompressing. It\'s recommended to only use this in combination with --verify')

		args = parser.parse_args()
		outfolder = str(Path(args.output)) if args.output else str(Path('.'))

		Print.info('')
		Print.info('             NSZ v2.1   ,;:;;,')
		Print.info('                       ;;;;;')
		Print.info('               .=\',    ;:;;:,')
		Print.info('              /_\', "=. \';:;:;')
		Print.info('              @=:__,  \,;:;:\'')
		Print.info('                _(\.=  ;:;;\'')
		Print.info('               `"_(  _/="`')
		Print.info('                `"\'')
		Print.info('')
		if args.extract:
			for filePath in args.extract:
				f = factory(filePath)
				f.open(filePath, 'rb')
				dir = Path(Path(filePath).name).suffix[0]
				f.unpack(dir)
				f.close()
		if args.create:
			Print.info('creating ' + args.create)
			nsp = Nsp.Nsp(None, None)
			nsp.path = args.create
			nsp.pack(args.file)
		if args.C:
			targetDict = CreateTargetDict(outfolder, args.parseCnmt, ".nsz")
			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsp'):
							if not AllowedToWriteOutfile(filePath, ".nsz", targetDict, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
							compress(filePath, args)

							if args.rm_source:
								delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when compressing file: %s' % filePath)
						err.append({"filename":filePath,"error":format_exc() })
						print_exc()


		if args.D:
			targetDict = CreateTargetDict(outfolder, args.parseCnmt, ".nsp")

			for i in args.file:
				for filePath in expandFiles(i):
					try:
						if filePath.endswith('.nsz'):
							if not AllowedToWriteOutfile(filePath, ".nsp", targetDict, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
							decompress(filePath, args.output)
							if args.rm_source:
								delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when decompressing file: %s' % filePath)
						err.append({"filename":filePath,"error":format_exc() })
						print_exc()

		if args.info:
			f = factory(args.info)
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
							verify(filePath, False)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when verifying file: %s' % filePath)
						err.append({"filename":filePath,"error":format_exc() })
						print_exc()

		if len(argv) == 1:
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

	Print.info('Done!')

if __name__ == '__main__':
	freeze_support()
	main()