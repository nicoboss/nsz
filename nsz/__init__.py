#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import path
from pathlib import Path

from sys import argv
from nsz.nut import Print
from os import listdir, _exit, remove
from time import sleep
from nsz.Fs import Nsp, Hfs0, factory
from nsz.BlockCompressor import blockCompress
from nsz.SolidCompressor import solidCompress
from traceback import print_exc, format_exc
from nsz.NszDecompressor import verify as NszVerify, decompress as NszDecompress, VerificationException
from multiprocessing import cpu_count, freeze_support, Process, Manager
from nsz.ThreadSafeCounter import Counter
from nsz.FileExistingChecks import CreateTargetDict, AllowedToWriteOutfile, delete_source_file
from nsz.ParseArguments import *
from nsz.PathTools import *
from nsz.ExtractTitlekeys import *
from nsz.undupe import undupe
import enlighten
import time
import sys

def solidCompressTask(in_queue, statusReport, readyForWork, pleaseNoPrint, pleaseKillYourself, id):
	while True:
		readyForWork.increment()
		item = in_queue.get()
		readyForWork.decrement()
		if pleaseKillYourself.value() > 0:
			break
		try:
			filePath, compressionLevel, outputDir, threadsToUse, verifyArg = item
			outFile = solidCompress(filePath, compressionLevel, outputDir, threadsToUse, statusReport, id, pleaseNoPrint)
			if verifyArg:
				Print.info("[VERIFY NSZ] {0}".format(outFile))
				try:
					verify(outFile, True, [statusReport, id], pleaseNoPrint)
				except VerificationException:
					Print.error("[BAD VERIFY] {0}".format(outFile))
					Print.error("[DELETE NSZ] {0}".format(outFile))
					remove(outFile)
		except KeyboardInterrupt:
			Print.info('Keyboard exception')
		except BaseException as e:
			Print.info('nut exception: {0}'.format(str(e)))
			raise

def compress(filePath, outputDir, args, work, amountOfTastkQueued):
	compressionLevel = 18 if args.level is None else args.level
	
	if filePath.suffix == ".xci" and not args.solid or args.block:
		threadsToUseForBlockCompression = args.threads if args.threads > 0 else cpu_count()
		outFile = blockCompress(filePath, compressionLevel, args.bs, outputDir, threadsToUseForBlockCompression)
		if args.verify:
			Print.info("[VERIFY NSZ] {0}".format(outFile))
			verify(outFile, True)
	else:
		threadsToUseForSolidCompression = args.threads if args.threads > 0 else 3
		work.put([filePath, compressionLevel, outputDir, threadsToUseForSolidCompression, args.verify])
		amountOfTastkQueued.increment()


def decompress(filePath, outputDir, statusReportInfo = None):
	NszDecompress(filePath, outputDir, statusReportInfo)

def verify(filePath, raiseVerificationException, statusReportInfo = None, pleaseNoPrint = None):
	NszVerify(filePath, raiseVerificationException, statusReportInfo, pleaseNoPrint)

err = []

def main():
	global err
	try:
		if len(argv) > 1:
			args = ParseArguments.parse()
		else:
			try:
				from nsz.gui.NSZ_GUI import GUI
			except ImportError:
				Print.error("Failed to import the GUI - is it installed?")
				return
			args = GUI().run()
			if args == None:
				Print.info("Done!")
				return
		
		if args.output:
			argOutFolderToPharse = args.output
			if not argOutFolderToPharse.endswith('/') and not argOutFolderToPharse.endswith('\\'):
				argOutFolderToPharse += "/"
			if not Path(argOutFolderToPharse).is_dir():
				Print.error('Error: Output directory "{0}" does not exist!'.format(args.output))
				return
		argOutFolder = Path(argOutFolderToPharse).resolve() if args.output else None
		
		Print.info('')
		Print.info('             NSZ v4.0   ,;:;;,')
		Print.info('                       ;;;;;')
		Print.info('               .=\',    ;:;;:,')
		Print.info('              /_\', "=. \';:;:;')
		Print.info('              @=:__,  \,;:;:\'')
		Print.info('                _(\.=  ;:;;\'')
		Print.info('               `"_(  _/="`')
		Print.info('                `"\'')
		Print.info('')
		
		barManager = enlighten.get_manager()
		poolManager = Manager()
		statusReport = poolManager.list()
		readyForWork = Counter(0)
		pleaseNoPrint = Counter(0)
		pleaseKillYourself = Counter(0)
		pool = []
		work = poolManager.Queue()
		amountOfTastkQueued = Counter(0)
		targetDictNsz = dict()
		targetDictXcz = dict()
		
		if args.titlekeys:
			extractTitlekeys(args.file)
		
		if args.extract:
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					filePath_str = str(filePath)
					outFolder = argOutFolder.joinpath(filePath.stem) if argOutFolder else filePath.parent.absolute().joinpath(filePath.stem)
					Print.info('Extracting "{0}" to {1}'.format(filePath_str, outFolder))
					container = factory(filePath)
					container.open(filePath_str, 'rb')
					if isXciXcz(filePath):
						for hfs0 in container.hfs0:
							secureIn = hfs0
							secureIn.unpack(outFolder.joinpath(hfs0._path), args.extractregex)
					else:
						container.unpack(outFolder, args.extractregex)
					container.close()

		if args.undupe or args.undupe_dryrun:
			undupe(args);

		if args.create:
			Print.info('Creating "{0}"'.format(args.create))
			nsp = Nsp.Nsp(None, None)
			nsp.path = args.create
			nsp.pack(args.file)

		if args.C:
			sourceFileToDelete = []
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					if not isUncompressedGame(filePath):
						continue
					try:
						outFolder = argOutFolder if argOutFolder else filePath.parent.absolute()
						if filePath.suffix == '.nsp':
							if not outFolder in targetDictNsz:
								targetDictNsz[outFolder] = CreateTargetDict(outFolder, args, ".nsz")
							if not AllowedToWriteOutfile(filePath, ".nsz", targetDictNsz[outFolder], args):
								continue
						elif filePath.suffix == '.xci':
							if not outFolder in targetDictXcz:
								targetDictXcz[outFolder] = CreateTargetDict(outFolder, args, ".xcz")
							if not AllowedToWriteOutfile(filePath, ".xcz", targetDictXcz[outFolder], args):
								continue
						compress(filePath, outFolder, args, work, amountOfTastkQueued)
						if args.rm_source:
							sourceFileToDelete.append(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error while compressing file: %s' % filePath)
						err.append({"filename":filePath,"error":format_exc() })
						print_exc()
			
			bars = []
			compressedSubBars = []
			BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
			parallelTasks = min(args.multi, amountOfTastkQueued.value())
			if parallelTasks < 0:
				parallelTasks = 4
			for i in range(parallelTasks):
				statusReport.append([0, 0, 100, 'Compressing'])
				p = Process(target=solidCompressTask, args=(work, statusReport, readyForWork, pleaseNoPrint, pleaseKillYourself, i))
				p.start()
				pool.append(p)
			for i in range(parallelTasks):
				bar = barManager.counter(total=100, desc='Compressing', unit='MiB', color='cyan', bar_format=BAR_FMT)
				compressedSubBars.append(bar.add_subcounter('green'))
				bars.append(bar)
			#Ensures that all threads are started and compleaded before being requested to quit
			while readyForWork.value() < parallelTasks:
				sleep(0.2)
				if pleaseNoPrint.value() > 0:
					continue
				pleaseNoPrint.increment()
				for i in range(parallelTasks):
					compressedRead, compressedWritten, total, currentStep = statusReport[i]
					if bars[i].total != total:
						bars[i].total = total//1048576
					bars[i].count = compressedRead//1048576
					compressedSubBars[i].count = compressedWritten//1048576
					bars[i].desc = currentStep
					bars[i].refresh()
				pleaseNoPrint.decrement()
			pleaseKillYourself.increment()
			for i in range(readyForWork.value()):
				work.put(None)
			
			while readyForWork.value() > 0:
				sleep(0.02)
			
			for i in range(parallelTasks):
				bars[i].close(clear=True)
			barManager.stop()

			for filePath in sourceFileToDelete:
				delete_source_file(filePath)

		if args.D:
			for f_str in args.file:
				for filePath in expandFiles(Path(f_str)):
					if not isCompressedGame(filePath) and not isCompressedGameFile(filePath):
						continue
					try:
						outFolder = argOutFolder if argOutFolder else filePath.parent.absolute()
						if filePath.suffix == '.nsz':
							if not outFolder in targetDictNsz:
								targetDictNsz[outFolder] = CreateTargetDict(outFolder, args, ".xcz")
							if not AllowedToWriteOutfile(filePath, ".nsp", targetDictNsz[outFolder], args):
								continue
						elif filePath.suffix == '.xcz':
							if not outFolder in targetDictXcz:
								targetDictXcz[outFolder] = CreateTargetDict(outFolder, args, ".xcz")
							if not AllowedToWriteOutfile(filePath, ".xci", targetDictXcz[outFolder], args):
								continue
						elif filePath.suffix == '.ncz':
							outFile = Path(changeExtension(outFolder.joinpath(filePath.name), ".nca"))
							if not args.overwrite and outFile.is_file():
								Print.info('{0} with the same file name already exists in the output directory.\n'\
								'If you want to overwrite it use the -w parameter!'.format(outFile.name))
								continue
						decompress(filePath, outFolder)
						if args.rm_source:
							delete_source_file(filePath)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error while decompressing file: {0}'.format(filePath))
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
							Print.info("[VERIFY {0}] {1}".format(getExtensionName(filePath), filePath.name))
							verify(filePath, True)
					except KeyboardInterrupt:
						raise
					except BaseException as e:
						Print.error('Error while verifying file: {0}'.format(filePath))
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
			Print.info('\033[0mError while processing {0}'.format(e["filename"]))
			Print.info(e["error"])

		Print.info('\nDone!\n')
		print()
		print()
		if len(argv) <= 1:
			input("Press Enter to exit...")	
		sys.exit(1)
	
	Print.info('\nDone!\n')
	if len(argv) <= 1:
		input("Press Enter to exit...")
	sys.exit(0)
	#breakpoint()


if __name__ == '__main__':
	freeze_support()
	main()
