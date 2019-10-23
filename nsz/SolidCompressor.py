from nut import Print, aes128
from nsz import SectionFs
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
import traceback
import fnmatch

def solidCompress(filePath, compressionLevel = 18, outputDir = None, threads = -1, overwrite = False, filesAtTarget = []):

	ncaHeaderSize = 0x4000
	
	filePath = os.path.abspath(filePath)
	container = Fs.factory(filePath)
	container.open(filePath, 'rb')
	
	CHUNK_SZ = 0x1000000
	
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
		if isinstance(nspf, Fs.Ticket.Ticket):
			nspf.getRightsId()
			titleId = nspf.titleId()
			break # No need to go for other objects

	# Checking output directory to see if the NSZ file with same title ID as NSP exists.
	potentiallyExistingNszFile = ''
	for file in filesAtTarget:
		if fnmatch.fnmatch(file, '*%s*.nsz' % titleId):
			potentiallyExistingNszFile = file

	# If the file exists and '-w' parameter is not used than don't compress
	if not overwrite:
		if os.path.isfile(nszPath):
			Print.info('{0} with the same file name already exists in the output directory.\n'\
			'If you want to overwrite it use the -w parameter!'.format(nszFilename))
			return
		if potentiallyExistingNszFile:
			potentiallyExistingNszFileName = os.path.basename(potentiallyExistingNszFile)
			Print.info('{0} with the same title ID {1} but a different filename already exists in the output directory.\n'\
			'If you want to continue with {2} keeping both files use the -w parameter!'
			.format(potentiallyExistingNszFileName, titleId, nszFilename))
			return

	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	
	newNsp = Fs.Pfs0.Pfs0Stream(nszPath)
	
	try:

		for nspf in container:

			if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.DATA:
				Print.info('skipping delta fragment')
				continue
				
			if isinstance(nspf, Fs.Nca.Nca) and (nspf.header.contentType == Fs.Type.Content.PROGRAM or nspf.header.contentType == Fs.Type.Content.PUBLICDATA):
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
					
					decompressedBytes = ncaHeaderSize
					
					with tqdm(total=nspf.size, unit_scale=True, unit="B/s") as bar:
						
						partitions = []
						for section in sections:
							#print('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
							partitions.append(nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
							
						
						partNr = 0
						bar.update(f.tell())
						cctx = zstandard.ZstdCompressor(level=compressionLevel)
						compressor = cctx.stream_writer(f)
						while True:
						
							buffer = partitions[partNr].read(CHUNK_SZ)
							while (len(buffer) < CHUNK_SZ and partNr < len(partitions)-1):
								partNr += 1
								buffer += partitions[partNr].read(CHUNK_SZ - len(buffer))
							if len(buffer) == 0:
								break
							compressor.write(buffer)
							
							decompressedBytes += len(buffer)
							bar.update(len(buffer))
					
					compressor.flush(zstandard.FLUSH_FRAME)
					compressor.flush(zstandard.COMPRESSOBJ_FLUSH_FINISH)
					
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
		
	except KeyboardInterrupt:
		newNsp.close()
		os.remove(nszPath)
		raise KeyboardInterrupt

	except BaseException as e:
		Print.error(traceback.format_exc())
		newNsp.close()
		os.remove(nszPath)
		
	return nszPath