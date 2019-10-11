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

def compress(filePath, compressionLevel = 17, outputDir = None):
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)
	
	container.open(filePath, 'rb')

	CHUNK_SZ = 0x1000000

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
				cctx = zstandard.ZstdCompressor(level=compressionLevel)

				newFileName = nspf._path[0:-1] + 'z'

				f = newNsp.add(newFileName, nspf.size)
				
				start = f.tell()

				nspf.seek(0)
				f.write(nspf.read(ncaHeaderSize))
				written = ncaHeaderSize

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
				written += len(header)
				
				decompressedBytes = ncaHeaderSize
					
				with tqdm(total=nspf.size, unit_scale=True, unit="B/s") as bar:
					for section in sections:
						#print('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
						o = nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True)
						
						while not o.eof():
							buffer = o.read(CHUNK_SZ)
							
							if len(buffer) == 0:
								raise IOError('read failed')

							written += compressor.write(buffer)
							
							decompressedBytes += len(buffer)
							bar.update(len(buffer))
						
				compressor.flush(zstandard.FLUSH_FRAME)
				
				print('%d written vs %d tell' % (written, f.tell() - start))
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
			
			start = f.tell()

			nspf.seek(0)
			
			header = nspf.read(ncaHeaderSize)
			magic = nspf.read(8)
			sectionCount = nspf.readInt64()
			sections = []
			for i in range(sectionCount):
				sections.append(Section(nspf))

			dctx = zstandard.ZstdDecompressor()
			reader = dctx.stream_reader(nspf)

			with tqdm(total=nspf.size, unit_scale=True, unit="B/s") as bar:
				f.write(header)
				bar.update(len(header))
				
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
						chunkSz = 0x10000 if end - i > 0x10000 else end - i
						buf = reader.read(chunkSz)
						
						if not len(buf):
							break
						
						#f.seek(i)
						f.write(crypto.encrypt(buf))
						bar.update(len(buf))
						
						i += chunkSz

			
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