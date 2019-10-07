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
import time

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

	next = 0x4000
	for i in range(len(fs)):
		if fs[i].offset != next:
			return False

		next = fs[i].offset + fs[i].size

	if next != nca.size:
		return False

	return True

def compress(filePath, compressionLevel = 17, outputDir = None, threads = 0):
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)

	container.open(filePath, 'rb')

	CHUNK_SZ = 0x1000000

	if outputDir is None:
		nszPath = filePath[0:-1] + 'z'
	else:
		nszPath = os.path.join(outputDir, os.path.basename(filePath[0:-1] + 'z'))
		
	nszPath = os.path.abspath(nszPath)
	
	Print.info('compressing (level %d, %d threads) %s -> %s' % (compressionLevel, threads, filePath, nszPath))
	
	newNsp = Fs.Pfs0.Pfs0Stream(nszPath)

	for nspf in container:
		if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.PROGRAM:
			if isNcaPacked(nspf):
				cctx = zstandard.ZstdCompressor(level=compressionLevel, threads = threads)

				newFileName = nspf._path[0:-1] + 'z'

				f = newNsp.add(newFileName, nspf.size)
				
				start = f.tell()

				nspf.seek(0)
				f.write(nspf.read(0x4000))
				written = 0x4000
				
				timestamp = time.time()

				compressor = cctx.stream_writer(f)
				
				header = b'NCZSECTN'
				header += len(sortedFs(nspf)).to_bytes(8, 'little')
				
				i = 0
				for fs in sortedFs(nspf):
					i += 1
					header += fs.realOffset().to_bytes(8, 'little')
					header += fs.size.to_bytes(8, 'little')
					header += fs.cryptoType.to_bytes(8, 'little')
					header += b'\x00' * 8
					header += fs.cryptoKey
					header += fs.cryptoCounter
					
				f.write(header)
				written += len(header)
				
				decompressedBytes = 0x4000

				for fs in sortedFs(nspf):
					fs.seek(0)

					while not fs.eof():
						buffer = fs.read(CHUNK_SZ)

						if len(buffer) == 0:
							raise IOError('read failed')

						written += compressor.write(buffer)
						
						decompressedBytes += len(buffer)
						
				compressor.flush(zstandard.FLUSH_FRAME)
				
				elapsed = time.time() - timestamp
				minutes = elapsed / 60
				seconds = elapsed % 60
				
				speed = 0 if elapsed == 0 else (nspf.size / elapsed)

				written = f.tell() - start
				print('\ncompressed %d%% %d -> %d  - %s' % (int(written * 100 / nspf.size), decompressedBytes, written, nspf._path))
				print('duration: %02d:%02d  speed: %.1f MB/s\n' % (minutes, seconds, speed / 1000000.0))
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
