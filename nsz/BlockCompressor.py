from os import remove
from nut import Print
from tqdm import tqdm
from time import sleep
from pathlib import Path
from traceback import format_exc
from zstandard import ZstdCompressor
from ThreadSafeCounter import Counter
from SectionFs import isNcaPacked, sortedFs
from multiprocessing import Process, Manager
from Fs import Pfs0, Hfs0, Nca, Type, Ticket, Xci, factory
from GameType import *

def compressBlockTask(in_queue, out_list, readyForWork, pleaseKillYourself):
	while True:
		readyForWork.increment()
		item = in_queue.get()
		readyForWork.decrement()
		if(pleaseKillYourself.value() > 0):
			break
		buffer, compressionLevel, compressedblockSizeList, chunkRelativeBlockID = item # compressedblockSizeList IS UNUSED VARIABLE
		if buffer == 0:
			return
		compressed = ZstdCompressor(level=compressionLevel).compress(buffer)
		out_list[chunkRelativeBlockID] = compressed if len(compressed) < len(buffer) else buffer

def blockCompress(filePath, compressionLevel = 18, blockSizeExponent = 20, outputDir = None, threads = -1):
	if filePath.endswith('.nsp'):
		return blockCompressNsp(filePath, compressionLevel, blockSizeExponent, outputDir, threads)
	elif filePath.endswith('.xci'):
		return blockCompressXci(filePath, compressionLevel, blockSizeExponent, outputDir, threads)

def blockCompressContainer(readContainer, writeContainer, compressionLevel, blockSizeExponent, threads):
	CHUNK_SZ = 0x100000
	ncaHeaderSize = 0x4000
	if blockSizeExponent < 14 or blockSizeExponent > 32:
		raise ValueError("Block size must be between 14 and 32")
	blockSize = 2**blockSizeExponent
	try:
		manager = Manager()
		results = manager.list()
		readyForWork = Counter(0)
		pleaseKillYourself = Counter(0)
		TasksPerChunk = 209715200//blockSize
		for i in range(TasksPerChunk):
			results.append(b"")
		work = manager.Queue(threads)
		pool = []

		for i in range(threads):
			p = Process(target=compressBlockTask, args=(work, results, readyForWork, pleaseKillYourself))
			p.start()
			pool.append(p)

		for nspf in readContainer:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
				Print.info('skipping delta fragment')
				continue
			if isinstance(nspf, Nca.Nca) and (nspf.header.contentType == Type.Content.PROGRAM or nspf.header.contentType == Type.Content.PUBLICDATA):
				if isNcaPacked(nspf, ncaHeaderSize):
					newFileName = nspf._path[0:-1] + 'z'
					f = writeContainer.add(newFileName, nspf.size)
					start = f.tell()
					nspf.seek(0)
					f.write(nspf.read(ncaHeaderSize))
					sections = []

					for fs in sortedFs(nspf):
						sections += fs.getEncryptionSections()

					if len(sections) == 0:
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
					bytesToCompress = nspf.size - ncaHeaderSize
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
					decompressedBytes = ncaHeaderSize
					with tqdm(total=nspf.size, unit_scale=True, unit="B") as bar:
						partitions = [nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True) for section in sections]
						partNr = 0
						bar.update(f.tell())
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
									compressedblockSizeList[startChunkBlockID+i] = len(results[i])
									f.write(results[i])
									results[i] = b""

								if len(buffer) == 0:
									pleaseKillYourself.increment()

									for i in range(readyForWork.value()):
										work.put(None)

									while readyForWork.value() > 0:
										sleep(0.02)
									break
								chunkRelativeBlockID = 0
								startChunkBlockID = blockID
							work.put([buffer, compressionLevel, compressedblockSizeList, chunkRelativeBlockID])
							blockID += 1
							chunkRelativeBlockID += 1
							decompressedBytes += len(buffer)
							bar.update(len(buffer))
					partitions[partNr].close()
					partitions[partNr] = None
					f.seek(blocksHeaderFilePos+24)
					header = b""

					for compressedblockSize in compressedblockSizeList:
						header += compressedblockSize.to_bytes(4, 'little')

					f.write(header)
					f.seek(0, 2) #Seek to end of file.
					written = f.tell() - start
					print('compressed %d%% %d -> %d  - %s' % (int(written * 100 / nspf.size), decompressedBytes, written, nspf._path))
					writeContainer.resize(newFileName, written)
					continue
				else:
					print('not packed!')
			f = writeContainer.add(nspf._path, nspf.size)
			nspf.seek(0)
			while not nspf.eof():
				buffer = nspf.read(CHUNK_SZ)
				f.write(buffer)
	except:
		pass


def blockCompressNsp(filePath, compressionLevel = 18, blockSizeExponent = 20, outputDir = None, threads = -1):
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	nszPath = changeExtension(filePath, '.nsz')
	if not outputDir == None:
		nszPath = Path(outputDir).joinpath(nszPath).resolve(strict=False)

	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	
	try:
		with Pfs0.Pfs0Stream(nszPath) as nsp:
			blockCompressContainer(container, nsp, compressionLevel, blockSizeExponent, threads)
	except KeyboardInterrupt:
		remove(nszPath)
		raise KeyboardInterrupt
	except BaseException:
		Print.error(format_exc())
		remove(nszPath)

	container.close()
	return nszPath
	
def blockCompressXci(filePath, compressionLevel = 18, blockSizeExponent = 20, outputDir = None, threads = -1):
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	secureIn = container.hfs0['secure']
	xczPath = changeExtension(filePath, '.xcz')
	if not outputDir == None:
		xczPath = Path(outputDir).joinpath(xczPath).resolve(strict=False)

	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, xczPath))
	
	try:
		print(filePath)
		with Xci.XciStream(xczPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0), xci.f.tell()) as secureOut:
				blockCompressContainer(secureIn, secureOut, compressionLevel, blockSizeExponent, threads)
			
			xci.hfs0.resize('secure', secureOut.actualSize)
	except KeyboardInterrupt:
		remove(xczPath)
		raise KeyboardInterrupt
	except BaseException:
		Print.error(format_exc())
		remove(xczPath)

	container.close()
	return xczPath
