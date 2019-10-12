#from Fs.Pfs0 import Pfs0Stream
from nut import Print
import os, io
import json
import Fs
import Fs.Pfs0
import Fs.Type
import Fs.Nca
import Fs.Type
import subprocess
from contextlib import closing
import zstandard
from tqdm import tqdm

ncaHeaderSize = 0x4000

def sortedFs(nca):
	fs = []
	for i in nca.sections:
		fs.append(i)
	fs.sort(key=lambda x: x.offset)
	return fs

def isNcaPacked(nca):
	fs = sortedFs(nca)

	if len(fs) == 0:
		return True

	next = ncaHeaderSize
	for i in range(len(fs)):
		if fs[i].offset != next:
			return False

		next = fs[i].offset + fs[i].size

	if next != nca.size:
		return False

	return True

def compress(filePath, compressionLevel = 17, solid = False, blockSizeExponent = 19, outputDir = None, threads = 0):
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)
	
	container.open(filePath, 'rb')

	CHUNK_SZ = 0x1000000
	
	useBlockCompression = not solid
	
	blockSize = -1
	if useBlockCompression:
		if blockSizeExponent < 14 or blockSizeExponent > 32:
			raise ValueError("block size must be between 14 and 32")
		blockSize = 2**blockSizeExponent

	if outputDir is None:
		nszPath = filePath[0:-1] + 'z'
	else:
		nszPath = os.path.join(outputDir, os.path.basename(filePath[0:-1] + 'z'))
		
	nszPath = os.path.abspath(nszPath)
	
	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	
	newNsp = Fs.Pfs0.Pfs0Stream(nszPath)

	

	for nspf in container:
		if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.DATA:
			Print.info('skipping delta fragment')
			continue
			
		if isinstance(nspf, Fs.Nca.Nca) and (nspf.header.contentType == Fs.Type.Content.PROGRAM or nspf.header.contentType == Fs.Type.Content.PUBLICDATA):
			if isNcaPacked(nspf):
				
				newFileName = nspf._path[0:-1] + 'z'
				
				f = newNsp.add(newFileName, nspf.size)
				f = io.open("../in.ncz", "wb")
				
				start = f.tell()
				
				nspf.seek(0)
				f.write(nspf.read(ncaHeaderSize))
				
				cctx = zstandard.ZstdCompressor(level=compressionLevel)
				compressor = cctx.stream_writer(f)
				
				sections = []
				for fs in sortedFs(nspf):
					sections += fs.getEncryptionSections()
				
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
				blocksHeaderFilePos = f.tell()
				compressedblockSizeList = []
				
				if useBlockCompression:
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
				
				decompressedBytes = ncaHeaderSize
				
				with tqdm(total=nspf.size, unit_scale=True, unit="B/s") as bar:
					
					partitions = []
					for section in sections:
						#print('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
						partitions.append(nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
						
					
					partNr = 0
					blockStartFilePos = f.tell()
					bar.update(blockStartFilePos)
					if not useBlockCompression:
						compressor = cctx.stream_writer(f)
					while True:
					
						if useBlockCompression:
							buffer = partitions[partNr].read(blockSize)
							while (len(buffer) < blockSize and partNr < len(partitions)-1):
								partNr += 1
								buffer += partitions[partNr].read(blockSize - len(buffer))
							if len(buffer) == 0:
								break
							compressor = cctx.stream_writer(f)
							compressor.write(buffer)
							compressor.flush(zstandard.FLUSH_FRAME)
							compressor.flush(zstandard.COMPRESSOBJ_FLUSH_FINISH)
							compressedblockSizeList.append(f.tell() - blockStartFilePos)
							blockID += 1
							blockStartFilePos = f.tell()
						else:
							buffer = partitions[partNr].read(CHUNK_SZ)
							while (len(buffer) < CHUNK_SZ and partNr < len(partitions)-1):
								partNr += 1
								buffer += partitions[partNr].read(CHUNK_SZ - len(buffer))
							if len(buffer) == 0:
								break
							compressor.write(buffer)
							
						decompressedBytes += len(buffer)
						bar.update(len(buffer))
				
				if not useBlockCompression:
					compressor.flush(zstandard.FLUSH_FRAME)
					compressor.flush(zstandard.COMPRESSOBJ_FLUSH_FINISH)

				if useBlockCompression:
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


	newNsp.close()
