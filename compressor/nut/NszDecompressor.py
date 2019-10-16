from nut import Print, Header, SectionFs, aes128
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
from time import sleep
from tqdm import tqdm
from binascii import hexlify as hx, unhexlify as uhx
import hashlib


def decompress(filePath, outputDir = None):
	
	ncaHeaderSize = 0x4000
	
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
				sections.append(Header.Section(nspf))

			pos = nspf.tell()
			blockMagic = nspf.read(8)
			nspf.seek(pos)
			useBlockCompression = blockMagic == b'NCZBLOCK'
			
			blockSize = -1
			if useBlockCompression:
				BlockHeader = Header.Block(nspf)
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
						if s.cryptoType in (3, 4):
							buf = crypto.encrypt(buf)
						f.write(buf)
						bar.update(len(buf))
						hash.update(buf)
						
						i += chunkSz
			
			if useBlockCompression and not decompressedBytes == BlockHeader.decompressedSize:
				Print.error("\nSomething went wrong! decompressedBytes != BlockHeader.decompressedSize:", decompressedBytes, "vs.", BlockHeader.decompressedSize)
			hexHash = hash.hexdigest()[0:32]
			print(hexHash + '.nca')
			print(newFileName)
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
