from nsz.nut import Print
from os import remove
from pathlib import Path
from traceback import format_exc
from nsz.SectionFs import isNcaPacked, sortedFs
from nsz.Fs import factory, Ticket, Pfs0, Hfs0, Nca, Type, Xci
from zstandard import FLUSH_FRAME, COMPRESSOBJ_FLUSH_FINISH, ZstdCompressor
from nsz.PathTools import *

UNCOMPRESSABLE_HEADER_SIZE = 0x4000
CHUNK_SZ = 0x1000000


def solidCompress(filePath, compressionLevel, outputDir, threads, statusReport, id, pleaseNoPrint):
	if filePath.suffix == '.nsp':
		return solidCompressNsp(filePath, compressionLevel, outputDir, threads, statusReport, id, pleaseNoPrint)
	elif filePath.suffix == '.xci':
		return solidCompressXci(filePath, compressionLevel, outputDir, threads, statusReport, id, pleaseNoPrint)
		
def processContainer(readContainer, writeContainer, compressionLevel, threads, statusReport, id, pleaseNoPrint):
	for nspf in readContainer:
		if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
			Print.info('[SKIPPED]    Delta fragment {0}'.format(nspf._path), pleaseNoPrint)
			continue
		if nspf._path.endswith('.cnmt.xml'):
			Print.info('[SKIPPED]    Content meta {0}'.format(nspf._path), pleaseNoPrint)
			continue
		if isinstance(nspf, Nca.Nca) and (nspf.header.contentType == Type.Content.PROGRAM or nspf.header.contentType == Type.Content.PUBLICDATA) and nspf.size > UNCOMPRESSABLE_HEADER_SIZE:
			if isNcaPacked(nspf):
				
				offsetFirstSection = sortedFs(nspf)[0].offset
				newFileName = nspf._path[0:-1] + 'z'
		
				with writeContainer.add(newFileName, nspf.size, pleaseNoPrint) as f:
					start = f.tell()
		
					nspf.seek(0)
					f.write(nspf.read(UNCOMPRESSABLE_HEADER_SIZE))
		
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
		
					decompressedBytes = UNCOMPRESSABLE_HEADER_SIZE
					
					
					statusReport[id] = [0, 0, nspf.size, 'Compressing']
					
					partitions = []
					if offsetFirstSection-UNCOMPRESSABLE_HEADER_SIZE > 0:
						partitions.append(nspf.partition(offset = UNCOMPRESSABLE_HEADER_SIZE, size = offsetFirstSection-UNCOMPRESSABLE_HEADER_SIZE, cryptoType = Type.Crypto.CTR.NONE, autoOpen = True))
					for section in sections:
						#Print.info('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))), pleaseNoPrint)
						partitions.append(nspf.partition(offset = section.offset, size = section.size, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True))
					if UNCOMPRESSABLE_HEADER_SIZE-offsetFirstSection > 0:
						partitions[0].seek(UNCOMPRESSABLE_HEADER_SIZE-offsetFirstSection)
					
					partNr = 0
					statusReport[id] = [nspf.tell(), f.tell(), nspf.size, 'Compressing']
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
						statusReport[id] = [nspf.tell(), f.tell(), nspf.size, 'Compressing']
					partitions[partNr].close()
					partitions[partNr] = None
		
					compressor.flush(FLUSH_FRAME)
					compressor.flush(COMPRESSOBJ_FLUSH_FINISH)
					statusReport[id] = [nspf.tell(), f.tell(), nspf.size, 'Compressing']
		
					written = f.tell() - start
					Print.info('Compressed {0}% {1} -> {2}  - {3}'.format(written * 100 / nspf.size, decompressedBytes, written, nspf._path), pleaseNoPrint)
					writeContainer.resize(newFileName, written)
					continue
			else:
				Print.info('Skipping not packed {0}'.format(nspf._path))

		with writeContainer.add(nspf._path, nspf.size, pleaseNoPrint) as f:
			nspf.seek(0)
			while not nspf.eof():
				buffer = nspf.read(CHUNK_SZ)
				f.write(buffer)


def solidCompressNsp(filePath, compressionLevel, outputDir, threads, statusReport, id, pleaseNoPrint):
	filePath = filePath.resolve()
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	nszPath = outputDir.joinpath(filePath.stem + '.nsz')

	Print.info('Solid compressing (level {0}) {1} -> {2}'.format(compressionLevel, filePath, nszPath), pleaseNoPrint)
	
	try:
		with Pfs0.Pfs0Stream(str(nszPath)) as nsp:
			processContainer(container, nsp, compressionLevel, threads, statusReport, id, pleaseNoPrint)
	except BaseException as ex:
		if not ex is KeyboardInterrupt:
			Print.error(format_exc())
		if nszPath.is_file():
			nszPath.unlink()

	container.close()
	return nszPath
	
def solidCompressXci(filePath, compressionLevel, outputDir, threads, statusReport, id, pleaseNoPrint):
	filePath = filePath.resolve()
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	secureIn = container.hfs0['secure']
	xczPath = outputDir.joinpath(filePath.stem + '.xcz')

	Print.info('Solid compressing (level {0}) {1} -> {2}'.format(compressionLevel, filePath, xczPath), pleaseNoPrint)
	
	try:
		with Xci.XciStream(str(xczPath), originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0, pleaseNoPrint), xci.f.tell()) as secureOut:
				processContainer(secureIn, secureOut, compressionLevel, threads, statusReport, id, pleaseNoPrint)
			
			xci.hfs0.resize('secure', secureOut.actualSize)
	except BaseException as ex:
		if not ex is KeyboardInterrupt:
			Print.error(format_exc())
		if xczPath.is_file():
			xczPath.unlink()

	container.close()
	return xczPath
