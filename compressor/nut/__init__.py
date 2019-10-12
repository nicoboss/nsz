#from Fs.Pfs0 import Pfs0Stream
from nut import Print
import os
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
from binascii import hexlify as hx, unhexlify as uhx
from nut import aes128
import hashlib

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
			raise ValueError("Block size must be between 14 and 32")
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
	
class Section:
	def __init__(self, f):
		self.f = f
		self.offset = f.readInt64()
		self.size = f.readInt64()
		self.cryptoType = f.readInt64()
		f.readInt64() # padding
		self.cryptoKey = f.read(16)
		self.cryptoCounter = f.read(16)
		
class Block:
	def __init__(self, f):
		self.f = f
		self.magic = f.read(8)
		self.version = readInt8(f)
		self.type = readInt8(f)
		self.unused = readInt8(f)
		self.blockSizeExponent = readInt8(f)
		self.numberOfBlocks = readInt32(f)
		self.decompressedSize = readInt64(f)
		self.compressedBlockSizeList = []
		for i in range(self.numberOfBlocks):
			self.compressedBlockSizeList.append(readInt32(f))

def decompress(filePath, outputDir = None):
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)
	
	container.open(filePath, 'rb')

	CHUNK_SZ = 0x1000000

	if outputDir is None:
		nspPath = filePath[0:-1] + 'p'
	else:
		nspPath = os.path.join(outputDir, os.path.basename(filePath[0:-1] + 'p'))
		
	nspPath = os.path.abspath(nspPath)
	
	Print.info('decompressing %s -> %s' % (filePath, nspPath))
	
	newNsp = Fs.Pfs0.Pfs0Stream(nspPath)

	for nspf in container:
		if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.DATA:
			Print.info('skipping delta fragment')
			continue
			
			
		if nspf._path.endswith('.ncz'):
			newFileName = nspf._path[0:-1] + 'a'

			f = newNsp.add(newFileName, nspf.size)
			
			start = nspf.tell()

			nspf.seek(0)
			
			header = nspf.read(ncaHeaderSize)
			magic = nspf.read(8)
			if not magic == b'NCZSECTN':
				raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
			sectionCount = nspf.readInt64()
			sections = []
			for i in range(sectionCount):
				sections.append(Section(nspf))

			pos = nspf.tell()
			blockMagic = nspf.read(8)
			nspf.seek(pos)
			useBlockCompression = blockMagic == b'NCZBLOCK'
			
			blockSize = -1
			if useBlockCompression:
				BlockHeader = Block(nspf)
				if BlockHeader.blockSizeExponent < 14 or BlockHeader.blockSizeExponent > 32:
					raise ValueError("Corrupted NCZBLOCK header: Block size must be between 14 and 32")
				blockSize = 2**BlockHeader.blockSizeExponent
			pos = nspf.tell()

			dctx = zstandard.ZstdDecompressor()
			if not useBlockCompression:
				decompressor = dctx.stream_reader(nspf)

			hash = hashlib.sha256()
			with tqdm(total=nspf.size, unit_scale=True, unit="B/s") as bar:
				f.write(header)
				bar.update(len(header))
				hash.update(header)
				
				for s in sections:
					if s.cryptoType == 1: #plain text
						continue
						
					if s.cryptoType not in (3, 4):
						raise IOError('unknown crypto type: %d' % s.cryptoType)
					
					i = s.offset
					
					crypto = aes128.AESCTR(s.cryptoKey, s.cryptoCounter)
					end = s.offset + s.size
					
					while i < end:
						#f.seek(i)
						crypto.seek(i)
						
						if useBlockCompression:
							decompressor = dctx.stream_reader(nspf)
							inputChunk = decompressor.read(blockSize)
							decompressedBytes += len(inputChunk)
							o.write(inputChunk)
							decompressor.flush()
							o.flush()
							print('Block', str(blockID+1)+'/'+str(BlockHeader.numberOfBlocks))
							pos += BlockHeader.compressedBlockSizeList[blockID]
							nspf.seek(pos)
							blockID += 1
							if(blockID >= len(BlockHeader.compressedBlockSizeList)):
								break
						else:
							chunkSz = 0x10000 if end - i > 0x10000 else end - i
							buf = decompressor.read(chunkSz)
						
						if not len(buf):
							break
						
						#f.seek(i)
						buf = crypto.encrypt(buf)
						f.write(buf)
						bar.update(len(buf))
						hash.update(buf)
						
						i += chunkSz
			
			if useBlockCompression and not decompressedBytes == BlockHeader.decompressedSize:
				Print.error("\nSomething went wrong! decompressedBytes != BlockHeader.decompressedSize:", decompressedBytes, "vs.", BlockHeader.decompressedSize)
			hexHash = hash.hexdigest()[0:32]
			if hexHash + '.nca' != newFileName:
				print(hexHash + '.nca')
				print(newFileName)
				Print.error('\nNCZ verification failed!\n')
			else:
				Print.info('\nNCZ verification successful!\n')

			
			end = f.tell()
			written = end - start

			newNsp.resize(newFileName, written)
			continue

		f = newNsp.add(nspf._path, nspf.size)
		nspf.seek(0)
		while not nspf.eof():
			buffer = nspf.read(CHUNK_SZ)
			f.write(buffer)


	newNsp.close()