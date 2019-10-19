from nut import Print, Header, SectionFs, BlockDecompressorReader, aes128
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

		if not nspf._path.endswith('.ncz'):
			f = newNsp.add(nspf._path, nspf.size)
			nspf.seek(0)
			while not nspf.eof():
				inputChunk = nspf.read(CHUNK_SZ)
				f.write(inputChunk)
			continue

		newFileName = nspf._path[0:-1] + 'a'
		f = newNsp.add(newFileName, nspf.size)
		start = f.tell()
		blockID = 0
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
			blockDecompressorReader = BlockDecompressorReader.BlockDecompressorReader(nspf, BlockHeader)
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
					chunkSz = 0x10000 if end - i > 0x10000 else end - i
					if useBlockCompression:
						inputChunk = blockDecompressorReader.read(chunkSz)
					else:
						inputChunk = decompressor.read(chunkSz)
					
					if not len(inputChunk):
						break
					
					#f.seek(i)
					if not useBlockCompression:
						decompressor.flush()
					if s.cryptoType in (3, 4):
						inputChunk = crypto.encrypt(inputChunk)
					f.write(inputChunk)
					bar.update(len(inputChunk))
					hash.update(inputChunk)
					
					i += len(inputChunk)
		
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
		written = (end - start)
		print("Written:", written)

		newNsp.resize(newFileName, written)
		continue
		
	newNsp.close()
