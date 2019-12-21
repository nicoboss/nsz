#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import path
from pathlib import Path
scriptPath = Path(__file__).resolve()
importPath_str = str(scriptPath.parent)
path.append(importPath_str)

from sys import argv
from nut import Print
from os import listdir
from Fs import Nsp, factory
from BlockCompressor import blockCompress
from SolidCompressor import solidCompress
from traceback import print_exc, format_exc
from NszDecompressor import verify as NszVerify, decompress as NszDecompress
from multiprocessing import cpu_count, freeze_support
from FileExistingChecks import CreateTargetDict, AllowedToWriteOutfile, delete_source_file
from ParseArguments import *
from PathTools import *
from ExtractTitlekeys import *

def compress(filePath, outputDir, args):
	compressionLevel = 22 if args.level is None else args.level
	threadsToUse = args.threads if args.threads > 0 else cpu_count()
	if filePath.suffix == ".xci" and not args.solid or args.block:
		outFile = blockCompress(filePath, compressionLevel, args.bs, outputDir, threadsToUse)
	else:
		if args.threads < 0:
			threadsToUse = 1
		outFile = solidCompress(filePath, compressionLevel, outputDir, threadsToUse)
	if args.verify:
		Print.info("[VERIFY NSZ] {0}".format(outFile))
		verify(outFile, True)

def decompress(filePath, outputDir):
	NszDecompress(filePath, outputDir)

def verify(filePath, raiseVerificationException):
	NszVerify(filePath, raiseVerificationException)

err = []

def main():
	global err
	try:
		
		if len(argv) > 1:
			args = ParseArguments.parse()
		else:
			from gui.NSZ_GUI import GUI
			args = GUI().run()
			if args == None:
				Print.info("Done!")
				return
		
		if args.output:
			outfolderToPharse = args.output
			if not outfolderToPharse.endswith('/') and not outfolderToPharse.endswith('\\'):
				outfolderToPharse += "/"
			if not Path(outfolderToPharse).is_dir():
				Print.error('Error: Output directory "{0}" does not exist!'.format(args.output))
				return
		outfolder = Path(outfolderToPharse).resolve() if args.output else Path('.').resolve()
		
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
		
		if args.titlekeys:
			extractTitlekeys(args.file)
		
		if args.extract:
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					filePath_str = str(filePath)
					Print.info('Extracting "{0}" to {1}'.format(filePath_str, outfolder))
					f = factory(filePath)
					f.open(filePath_str, 'rb')
					dir = outfolder.joinpath(filePath.stem)
					f.unpack(dir, args.extractregex)
					f.close()
		if args.create:
			Print.info('Creating "{0}"'.format(args.create))
			nsp = Nsp.Nsp(None, None)
			nsp.path = args.create
			nsp.pack(args.file)
		if args.C:
			targetDictNsz = CreateTargetDict(outfolder, args.parseCnmt, ".nsz")
			targetDictXcz = CreateTargetDict(outfolder, args.parseCnmt, ".xcz")
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					if not isUncompressedGame(filePath):
						continue
					try:
						if filePath.suffix == '.nsp':
							if not AllowedToWriteOutfile(filePath, ".nsz", targetDictNsz, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
						elif filePath.suffix == '.xci':
							if not AllowedToWriteOutfile(filePath, ".xcz", targetDictXcz, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
						compress(filePath, outfolder, args)
						if args.rm_source:
							delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when compressing file: %s' % filePath)
						err.append({"filename":filePath,"error":format_exc() })
						print_exc()


		if args.D:
			targetDictNsz = CreateTargetDict(outfolder, args.parseCnmt, ".nsp")
			targetDictXcz = CreateTargetDict(outfolder, args.parseCnmt, ".xci")
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					if not isCompressedGame(filePath) and not isCompressedGameFile(filePath):
						continue
					try:
						if filePath.suffix == '.nsz':
							if not AllowedToWriteOutfile(filePath, ".nsp", targetDictNsz, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
						elif filePath.suffix == '.xcz':
							if not AllowedToWriteOutfile(filePath, ".xci", targetDictXcz, args.rm_old_version, args.overwrite, args.parseCnmt):
								continue
						elif filePath.suffix == '.ncz':
							outfile = changeExtension(outfolder.joinpath(filePath.name), ".nca")
							if not args.overwrite and outfile.is_file():
								Print.info('{0} with the same file name already exists in the output directory.\n'\
								'If you want to overwrite it use the -w parameter!'.format(outfile.name))
								continue
						decompress(filePath, outfolder)
						if args.rm_source:
							delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when decompressing file: {0}'.format(filePath))
						err.append({"filename":filePath, "error":format_exc()})
						print_exc()

		if args.info:
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					filePath_str = str(filePath)
					Print.info(filePath_str)
					f = factory(filePath)
					f.open(filePath_str, 'r+b')
					f.printInfo(args.depth+1)
					f.close()
		if args.verify and not args.C and not args.D:
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					try:
						if isGame(filePath):
							Print.info("[VERIFY {0}] {1}".format(getExtensionName(filePath), f_str))
							verify(filePath, False)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error when verifying file: {0}'.format(filePath))
						err.append({"filename":filePath,"error":format_exc()})
						print_exc()

		if len(argv) == 1:
			pass
	except KeyboardInterrupt:
		Print.info('Keyboard exception')
	except BaseException as e:
		Print.info('nut exception: {0}'.format(str(e)))
		raise
	if err:
		Print.info('\n\033[93m\033[1mSummary of errors which occurred while processing files:')
		
		for e in err:
			Print.info('\033[0mError when processing {0}'.format(e["filename"]))
			Print.info(e["error"])

	Print.info('Done!')
	


if __name__ == '__main__':
	freeze_support()
	main()