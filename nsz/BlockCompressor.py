from nsz.nut import Print, aes128
from nsz import SectionFs, ThreadSafeCounter
import os
import json
import nsz.Fs
import nsz.Fs.Pfs0
import nsz.Fs.Nca
import nsz.Fs.Type
import subprocess
from contextlib import closing
import zstandard
import multiprocessing
from multiprocessing import Process, Manager
from time import sleep
from tqdm import tqdm
from binascii import hexlify as hx, unhexlify as uhx
import hashlib
import traceback
import fnmatch

def compressBlockTask(in_queue, out_list, blockSize, readyForWork, pleaseKillYourself):
	while True:
		readyForWork.increment()
		item = in_queue.get()
		readyForWork.decrement()
		if(pleaseKillYourself.value() > 0):
			break
		buffer, compressionLevel, compressedblockSizeList, chunkRelativeBlockID = item
		
		if buffer == 0:
			return
		
		cctx = zstandard.ZstdCompressor(level=compressionLevel)
		compressed = cctx.compress(buffer)
		
		#print(compressed)
		#We don't use len(buffer) to alwys compress smaller last blocks
		#So CompressedBlockSizeList[blockID] == blockSize is always uncompressed
		if len(compressed) < len(buffer):
			out_list[chunkRelativeBlockID] = compressed
		else:
			out_list[chunkRelativeBlockID] = buffer



def blockCompress(filePath, compressionLevel = 18, blockSizeExponent = 20, threads = 32, outputDir = None, overwrite = False, filesAtTarget = []):
	
	ncaHeaderSize = 0x4000
	
	if blockSizeExponent < 14 or blockSizeExponent > 32:
		raise ValueError("Block size must be between 14 and 32")
	blockSize = 2**blockSizeExponent
	
	filePath = os.path.abspath(filePath)
	container = nsz.Fs.factory(filePath)
	container.open(filePath, 'rb')

	CHUNK_SZ = 0x100000


	if outputDir is None:
		nszPath = filePath[0:-1] + 'z'
	else:
		nszPath = os.path.join(outputDir, os.path.basename(filePath[0:-1] + 'z'))

	nszPath = os.path.abspath(nszPath)
	nszFilename = os.path.basename(nszPath)

	# Getting title ID to check for NSZ file in the output directory
	# We should still keep this part of title ID comparison because not all files have titleID in
	# filename.
	titleId = ''
	for nspf in container:
		if isinstance(nspf, nsz.Fs.Ticket.Ticket):
			nspf.getRightsId()
			titleId = nspf.titleId()
			break # No need to go for other objects

	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	
	newNsp = nsz.Fs.Pfs0.Pfs0Stream(nszPath)

	try:
	
		manager = Manager()
		results = manager.list()
		readyForWork = ThreadSafeCounter.Counter(0)
		pleaseKillYourself = ThreadSafeCounter.Counter(0)
		TasksPerChunk = 209715200//blockSize
		for i in range(TasksPerChunk):
			results.append(b"")
		work = manager.Queue(threads)
		pool = []
		for i in range(threads):
			p = Process(target=compressBlockTask, args=(work, results, blockSize, readyForWork, pleaseKillYourself))
			p.start()
			pool.append(p)
	
		for nspf in container:
			if isinstance(nspf, nsz.Fs.Nca.Nca) and nspf.header.contentType == nsz.Fs.Type.Content.DATA:
				Print.info('skipping delta fragment')
				continue
				
			if isinstance(nspf, nsz.Fs.Nca.Nca) and (nspf.header.contentType == nsz.Fs.Type.Content.PROGRAM or nspf.header.contentType == nsz.Fs.Type.Content.PUBLICDATA):
				if SectionFs.isNcaPacked(nspf, ncaHeaderSize):
					
					newFileName = nspf._path[0:-1] + 'z'
					
					f = newNsp.add(newFileName, nspf.size)
					
					start = f.tell()
					
					nspf.seek(0)
					f.write(nspf.read(ncaHeaderSize))
					
					sections = []
					for fs in SectionFs.sortedFs(nspf):
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
					compressedblockSizeList = []
					
					bytesToCompress = nspf.size-0x4000
					blocksToCompress = bytesToCompress//blockSize + (bytesToCompress%blockSize > 0)
					header = b'NCZBLOCK' #Magic
					header += b'\x02' #Version
					header += b'\x01' #Type
					header += b'\x00' #Unused
					header += blockSizeExponent.to_bytes(1, 'little') #blockSizeExponent in bits: 2^x
					header += blocksToCompress.to_bytes(4, 'little') #Amount of Blocks
					header += bytesToCompress.to_bytes(8, 'little') #Decompressed Size
					header += b'\x00' * (blocksToCompress*4)
					f.write(header)
					compressedblockSizeList = [0]*blocksToCompress
					
					decompressedBytes = ncaHeaderSize
					
					with tqdm(total=nspf.size, unit_scale=True, unit="B") as bar:
						
						partitions = []
						for section in sections:
							#print('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
							partitions.append(nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
							
						
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
					newNsp.resize(newFileName, written)
					continue
				else:
					print('not packed!')

			f = newNsp.add(nspf._path, nspf.size)
			nspf.seek(0)
			while not nspf.eof():
				buffer = nspf.read(CHUNK_SZ)
				f.write(buffer)
		
	except KeyboardInterrupt:
		os.remove(nszPath)
		raise KeyboardInterrupt

	except BaseException as e:
		Print.error(traceback.format_exc())
		os.remove(nszPath)
	finally:
		newNsp.close()
		container.close()
		
	return nszPath
