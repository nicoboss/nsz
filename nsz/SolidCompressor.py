from nut import Print
from os import remove
from tqdm import tqdm
from pathlib import Path
from traceback import format_exc
from SectionFs import isNcaPacked, sortedFs
from Fs import factory, Ticket, Pfs0, Hfs0, Nca, Type, Xci
from zstandard import FLUSH_FRAME, COMPRESSOBJ_FLUSH_FINISH, ZstdCompressor
from GameType import *

ncaHeaderSize = 0x4000
CHUNK_SZ = 0x1000000

def solidCompress(filePath, compressionLevel = 18, outputDir = None, threads = -1):
	if filePath.endswith('.nsp'):
		return solidCompressNsp(filePath, compressionLevel, outputDir, threads)
	elif filePath.endswith('.xci'):
		return solidCompressXci(filePath, compressionLevel, outputDir, threads)
		
def processContainer(readContainer, writeContainer, compressionLevel, threads):
	for nspf in readContainer:
		if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
			Print.info('skipping delta fragment')
			continue
	
		if isinstance(nspf, Nca.Nca) and (nspf.header.contentType == Type.Content.PROGRAM or nspf.header.contentType == Type.Content.PUBLICDATA):
			if isNcaPacked(nspf, ncaHeaderSize):
		
				newFileName = nspf._path[0:-1] + 'z'
		
				with writeContainer.add(newFileName, nspf.size) as f:
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
					compressedblockSizeList = []
		
					decompressedBytes = ncaHeaderSize
		
					with tqdm(total=nspf.size, unit_scale=True, unit="B") as bar:
			
						partitions = []
						for section in sections:
							#print('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
							partitions.append(nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
				
			
						partNr = 0
						bar.update(f.tell())
						if threads > 1:
							cctx = ZstdCompressor(level=compressionLevel, threads=threads)
						else:
							cctx = ZstdCompressor(level=compressionLevel)
						compressor = cctx.stream_writer(f)
						while True:
			
							buffer = partitions[partNr].read(CHUNK_SZ)
							while (len(buffer) < CHUNK_SZ and partNr < len(partitions)-1):
								partitions[partNr].close()
								partitions[partNr] = None
								partNr += 1
								buffer += partitions[partNr].read(CHUNK_SZ - len(buffer))
							if len(buffer) == 0:
								break
							compressor.write(buffer)
				
							decompressedBytes += len(buffer)
							bar.update(len(buffer))
						partitions[partNr].close()
						partitions[partNr] = None
		
					compressor.flush(FLUSH_FRAME)
					compressor.flush(COMPRESSOBJ_FLUSH_FINISH)
		
					written = f.tell() - start
					print('compressed %d%% %d -> %d  - %s' % (int(written * 100 / nspf.size), decompressedBytes, written, nspf._path))
					writeContainer.resize(newFileName, written)
					continue
			else:
				print('not packed!')

		with writeContainer.add(nspf._path, nspf.size) as f:
			nspf.seek(0)
			while not nspf.eof():
				buffer = nspf.read(CHUNK_SZ)
				f.write(buffer)


def solidCompressNsp(filePath, compressionLevel = 18, outputDir = None, threads = -1):
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	nszPath = changeExtension(filePath, '.nsz')
	if not outputDir == None:
		nszPath = Path(outputDir).joinpath(nszPath).resolve(strict=False)

	Print.info('Solid compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	
	try:
		with Pfs0.Pfs0Stream(nszPath) as nsp:
			processContainer(container, nsp, compressionLevel, threads)
	except KeyboardInterrupt:
		remove(nszPath)
		raise KeyboardInterrupt
	except BaseException:
		Print.error(format_exc())
		remove(nszPath)

	container.close()
	return nszPath
	
def solidCompressXci(filePath, compressionLevel = 18, outputDir = None, threads = -1):
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	secureIn = container.hfs0['secure']
	xczPath = changeExtension(filePath, '.xcz')
	if not outputDir == None:
		xczPath = Path(outputDir).joinpath(xczPath).resolve(strict=False)

	Print.info('Solid compressing (level %d) %s -> %s' % (compressionLevel, filePath, xczPath))
	
	try:
		with Xci.XciStream(xczPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0), xci.f.tell()) as secureOut:
				processContainer(secureIn, secureOut, compressionLevel, threads)
			
			xci.hfs0.resize('secure', secureOut.actualSize)
	except KeyboardInterrupt:
		remove(xczPath)
		raise KeyboardInterrupt
	except BaseException:
		Print.error(format_exc())
		remove(xczPath)

	container.close()
	return xczPath