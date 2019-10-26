from nut import Print, aes128
from nsz import Header, SectionFs, BlockDecompressorReader
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
	__decompress(filePath, outputDir, True, False)

def verify(filePath, raiseVerificationException):
	__decompress(filePath, None, False, raiseVerificationException)

def __decompress(filePath, outputDir = None, write = True, raiseVerificationException = False):
	
	ncaHeaderSize = 0x4000
	CHUNK_SZ = 0x100000
	
	if write:
		if outputDir is None:
			nspPath = filePath[0:-1] + 'p'
		else:
			nspPath = os.path.join(outputDir, os.path.basename(filePath[0:-1] + 'p'))
			
		nspPath = os.path.abspath(nspPath)
		
		Print.info('decompressing %s -> %s' % (filePath, nspPath))
		
		newNsp = Fs.Pfs0.Pfs0Stream(nspPath)
	
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)
	
	container.open(filePath, 'rb')
	
	
	for nspf in container:
		if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.DATA:
			Print.info('skipping delta fragment')
			continue

		if not nspf._path.endswith('.ncz'):
			verifyFile = nspf._path.endswith('.nca') and not nspf._path.endswith('.cnmt.nca')
			if write:
				f = newNsp.add(nspf._path, nspf.size)
			hash = hashlib.sha256()
			nspf.seek(0)
			while not nspf.eof():
				inputChunk = nspf.read(CHUNK_SZ)
				hash.update(inputChunk)
				if write:
					f.write(inputChunk)
			hexHash = hash.hexdigest()[0:32]
			if verifyFile:
				if hexHash + '.nca' == nspf._path:
					Print.error('[VERIFIED]   {0}'.format(nspf._path))
				else:
					Print.info('[CORRUPTED]  {0}'.format(nspf._path))
					if raiseVerificationException:
						raise Exception("Verification detected hash missmatch!")
			elif not write:
				Print.info('[EXISTS]     {0}'.format(nspf._path))
			continue

		newFileName = nspf._path[0:-1] + 'a'
		if write:
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
			if write:
				f.write(header)
			bar.update(len(header))
			hash.update(header)
			
			for s in sections:
				i = s.offset
				
				crypto = aes128.AESCTR(s.cryptoKey, s.cryptoCounter)
				end = s.offset + s.size
				
				while i < end:
					crypto.seek(i)
					chunkSz = 0x10000 if end - i > 0x10000 else end - i
					if useBlockCompression:
						inputChunk = blockDecompressorReader.read(chunkSz)
					else:
						inputChunk = decompressor.read(chunkSz)
					
					if not len(inputChunk):
						break
					
					if not useBlockCompression:
						decompressor.flush()
					if s.cryptoType in (3, 4):
						inputChunk = crypto.encrypt(inputChunk)
					if write:
						f.write(inputChunk)
					bar.update(len(inputChunk))
					hash.update(inputChunk)
					
					i += len(inputChunk)

		hexHash = hash.hexdigest()[0:32]
		if hexHash + '.nca' == newFileName:
			Print.error('[VERIFIED]   {0}'.format(nspf._path))
		else:
			Print.info('[CORRUPTED]  {0}'.format(nspf._path))
			if raiseVerificationException:
				raise Exception("Verification detected hash missmatch")

		
		if write:
			end = f.tell()
			written = (end - start)
			newNsp.resize(newFileName, written)
		
		continue

	if write:
		newNsp.close()
