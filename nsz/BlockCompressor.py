from os import remove
from nsz.nut import Print
from time import sleep
from pathlib import Path
from traceback import format_exc
from zstandard import ZstdCompressionParameters, ZstdCompressor
from nsz.SectionFs import isNcaPacked, sortedFs
from multiprocessing import Process, Manager
from nsz.Fs import Pfs0, Hfs0, Nca, Type, Ticket, Xci, factory
from nsz.PathTools import *
import enlighten
import sys

if hasattr(sys, 'getandroidapilevel'):
    from nsz.ThreadSafeCounterManager import Counter
else:
    from nsz.ThreadSafeCounterSharedMemory import Counter


def compressBlockTask(in_queue, out_list, readyForWork, pleaseKillYourself, blockSize):
	while True:
		readyForWork.increment()
		item = in_queue.get()
		#readyForWork.decrement() # https://github.com/nicoboss/nsz/issues/80
		if pleaseKillYourself.value() > 0:
			break
		buffer, compressionLevel, useLongDistanceMode, chunkRelativeBlockID = item
		if buffer == 0:
			return
		if compressionLevel == 0 and len(buffer) == blockSize: # https://github.com/nicoboss/nsz/issues/79
			out_list[chunkRelativeBlockID] = buffer
		else:
			params = ZstdCompressionParameters.from_level(compressionLevel, enable_ldm=useLongDistanceMode)
			compressed = ZstdCompressor(compression_params=params).compress(buffer)
			out_list[chunkRelativeBlockID] = compressed if len(compressed) < len(buffer) else buffer

def blockCompress(filePath, compressionLevel, keep, fixPadding, useLongDistanceMode, blockSizeExponent, outputDir, threads):
	if filePath.suffix == '.nsp':
		return blockCompressNsp(filePath, compressionLevel, keep, fixPadding, useLongDistanceMode, blockSizeExponent, outputDir, threads)
	elif filePath.suffix == '.xci':
		return blockCompressXci(filePath, compressionLevel, keep, fixPadding, useLongDistanceMode, blockSizeExponent, outputDir, threads)

def blockCompressContainer(readContainer, writeContainer, compressionLevel, keep, useLongDistanceMode, blockSizeExponent, threads):
	CHUNK_SZ = 0x100000
	UNCOMPRESSABLE_HEADER_SIZE = 0x4000
	if blockSizeExponent < 14 or blockSizeExponent > 32:
		raise ValueError("Block size must be between 14 and 32")
	blockSize = 2**blockSizeExponent
	manager = Manager()
	results = manager.list()
	readyForWork = Counter(manager, 0)
	pleaseKillYourself = Counter(manager, 0)
	TasksPerChunk = 209715200//blockSize
	for i in range(TasksPerChunk):
		results.append(b"")
	pool = []
	work = manager.Queue(threads)
	
	for i in range(threads):
		p = Process(target=compressBlockTask, args=(work, results, readyForWork, pleaseKillYourself, blockSize))
		p.start()
		pool.append(p)

	for nspf in readContainer:
		if not keep:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
				Print.info('[SKIPPED]    Delta fragment {0}'.format(nspf._path))
				continue
		if isinstance(nspf, Nca.Nca) and (nspf.header.contentType == Type.Content.PROGRAM or nspf.header.contentType == Type.Content.PUBLICDATA) and nspf.size > UNCOMPRESSABLE_HEADER_SIZE:
			if isNcaPacked(nspf):
				
				offsetFirstSection = sortedFs(nspf)[0].offset
				newFileName = nspf._path[0:-1] + 'z'
				f = writeContainer.add(newFileName, nspf.size)
				startPos = f.tell()
				nspf.seek(0)
				f.write(nspf.read(UNCOMPRESSABLE_HEADER_SIZE))
				sections = []

				for fs in sortedFs(nspf):
					sections += fs.getEncryptionSections()

				if len(sections) == 0:
					for p in pool:
						#Process.terminate() might corrupt the datastructure but we do't care
						p.terminate()
					raise Exception("NCA can't be decrypted. Outdated keys.txt?")
				header = b'NCZSECTN'
				header += len(sections).to_bytes(8, 'little')
				i = 0

				for fs in sections:
					i += 1
					header += fs.offset.to_bytes(8, 'little')
					header += fs.size.to_bytes(8, 'little')
					header += fs.cryptoType.to_bytes(8, 'little')
					header += b'\x00' * 8
					header += fs.cryptoKey
					header += fs.cryptoCounter

				f.write(header)
				blockID = 0
				chunkRelativeBlockID = 0
				startChunkBlockID = 0
				blocksHeaderFilePos = f.tell()
				bytesToCompress = nspf.size - UNCOMPRESSABLE_HEADER_SIZE
				blocksToCompress = bytesToCompress//blockSize + (bytesToCompress%blockSize > 0)
				compressedblockSizeList = [0]*blocksToCompress
				header = b'NCZBLOCK' #Magic
				header += b'\x02' #Version
				header += b'\x01' #Type
				header += b'\x00' #Unused
				header += blockSizeExponent.to_bytes(1, 'little') #blockSizeExponent in bits: 2^x
				header += blocksToCompress.to_bytes(4, 'little') #Amount of Blocks
				header += bytesToCompress.to_bytes(8, 'little') #Decompressed Size
				header += b'\x00' * (blocksToCompress*4)
				f.write(header)
				decompressedBytes = UNCOMPRESSABLE_HEADER_SIZE
				compressedBytes = f.tell()
				BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
				bar = enlighten.Counter(total=nspf.size//1048576, desc='Compressing', unit='MiB', color='cyan', bar_format=BAR_FMT)
				subBars = bar.add_subcounter('green', all_fields=True)
				
				partitions = []
				if offsetFirstSection-UNCOMPRESSABLE_HEADER_SIZE > 0:
					partitions.append(nspf.partition(offset = UNCOMPRESSABLE_HEADER_SIZE, size = offsetFirstSection-UNCOMPRESSABLE_HEADER_SIZE, cryptoType = Type.Crypto.CTR.NONE, autoOpen = True))
				for section in sections:
					#Print.info('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
					partitions.append(nspf.partition(offset = section.offset, size = section.size, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
				if UNCOMPRESSABLE_HEADER_SIZE-offsetFirstSection > 0:
						partitions[0].seek(UNCOMPRESSABLE_HEADER_SIZE-offsetFirstSection)
				
				partNr = 0
				decompressedBytesOld = nspf.tell()//1048576
				bar.count = nspf.tell()//1048576
				subBars.count = f.tell()//1048576
				bar.refresh()
				while True:
					buffer = partitions[partNr].read(blockSize)
					while (len(buffer) < blockSize and partNr < len(partitions)-1):
						partitions[partNr].close()
						partitions[partNr] = None
						partNr += 1
						buffer += partitions[partNr].read(blockSize - len(buffer))
					if chunkRelativeBlockID >= TasksPerChunk or len(buffer) == 0:
						while readyForWork.value() < threads:
							sleep(0.02)

						for i in range(min(TasksPerChunk, blocksToCompress-startChunkBlockID)):
							lenResult = len(results[i])
							compressedBytes += lenResult
							compressedblockSizeList[startChunkBlockID+i] = lenResult
							f.write(results[i])
							results[i] = b""

						if len(buffer) == 0:
							break
						chunkRelativeBlockID = 0
						startChunkBlockID = blockID
					work.put([buffer, compressionLevel, useLongDistanceMode, chunkRelativeBlockID])
					readyForWork.decrement()
					blockID += 1
					chunkRelativeBlockID += 1
					decompressedBytes += len(buffer)
					if decompressedBytes - decompressedBytesOld > 10485760: #Refresh every 10 MB
						decompressedBytesOld = decompressedBytes
						bar.count = decompressedBytes//1048576
						subBars.count = compressedBytes//1048576
						bar.refresh()
				partitions[partNr].close()
				partitions[partNr] = None
				endPos = f.tell()
				bar.count = decompressedBytes//1048576
				subBars.count = compressedBytes//1048576
				bar.close()
				written = endPos - startPos
				f.seek(blocksHeaderFilePos+24)
				header = b""

				for compressedblockSize in compressedblockSizeList:
					header += compressedblockSize.to_bytes(4, 'little')

				f.write(header)
				f.seek(endPos) #Seek to end of file.
				Print.info('compressed %d%% %d -> %d  - %s' % (int(written * 100 / nspf.size), decompressedBytes, written, nspf._path))
				writeContainer.resize(newFileName, written)
				continue
			else:
				Print.info('Skipping not packed {0}'.format(nspf._path))
		f = writeContainer.add(nspf._path, nspf.size)
		nspf.seek(0)
		while not nspf.eof():
			buffer = nspf.read(CHUNK_SZ)
			f.write(buffer)

	#Ensures that all threads are started and compleaded before being requested to quit
	while readyForWork.value() < threads:
		sleep(0.02)
	pleaseKillYourself.increment()

	for i in range(readyForWork.value()):
		work.put(None)
		readyForWork.decrement()

	while readyForWork.value() > 0:
		sleep(0.02)


def blockCompressNsp(filePath, compressionLevel, keep, fixPadding, useLongDistanceMode, blockSizeExponent, outputDir, threads):
	filePath = filePath.resolve()
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	nszPath = outputDir.joinpath(filePath.stem + '.nsz')

	Print.info(f'Block compressing (level {compressionLevel}{" ldm" if useLongDistanceMode else ""}) {filePath} -> {nszPath}')
	
	try:
		with Pfs0.Pfs0Stream(container.getPaddedHeaderSize() if fixPadding else container.getFirstFileOffset(), None if fixPadding else container.getStringTableSize(), str(nszPath)) as nsp:
			blockCompressContainer(container, nsp, compressionLevel, keep, useLongDistanceMode, blockSizeExponent, threads)
	except BaseException as ex:
		if not ex is KeyboardInterrupt:
			Print.error(format_exc())
		if nszPath.is_file():
			nszPath.unlink()

	container.close()
	return nszPath

def allign0x200(n):
	return 0x200-n%0x200

def blockCompressXci(filePath, compressionLevel, keep, fixPadding, useLongDistanceMode, blockSizeExponent, outputDir, threads):
	filePath = filePath.resolve()
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	xczPath = outputDir.joinpath(filePath.stem + '.xcz')

	Print.info(f'Block compressing (level {compressionLevel}{" ldm" if useLongDistanceMode else ""}) {filePath} -> {xczPath}')
	
	try:
		with Xci.XciStream(str(xczPath), originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			for partitionIn in container.hfs0:
				xci.hfs0.written = False
				hfsPartitionOut = xci.hfs0.add(partitionIn._path, 0)
				with Hfs0.Hfs0Stream(hfsPartitionOut, xci.f) as partitionOut:
					if keep == True or partitionIn._path == 'secure':
						blockCompressContainer(partitionIn, partitionOut, compressionLevel, keep, useLongDistanceMode, blockSizeExponent, threads)
					alignedSize = partitionOut.actualSize + allign0x200(partitionOut.actualSize)
					xci.hfs0.resize(partitionIn._path, alignedSize)
					print(f'[RESIZE]     {partitionIn._path} to {hex(alignedSize)}')
					xci.hfs0.addpos += alignedSize
	except BaseException as ex:
		if not ex is KeyboardInterrupt:
			Print.error(format_exc())
		if xczPath.is_file():
			xczPath.unlink()

	container.close()
	return xczPath
