from nut import Print
from os import remove
from tqdm import tqdm
from pathlib import Path
from traceback import format_exc
from SectionFs import isNcaPacked, sortedFs
from Fs import factory, Ticket, Pfs0, Nca, Type
from zstandard import FLUSH_FRAME, COMPRESSOBJ_FLUSH_FINISH, ZstdCompressor

def solidCompress(filePath, compressionLevel = 18, outputDir = None, threads = -1):
	ncaHeaderSize = 0x4000
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	CHUNK_SZ = 0x1000000
	nszPath = str(Path(filePath[0:-1] + 'z' if outputDir == None else Path(outputDir).joinpath(Path(filePath[0:-1] + 'z').name)).resolve(strict=False))

	for nspf in container:
		if isinstance(nspf, Ticket.Ticket):
			nspf.getRightsId()
			break # No need to go for other objects

	Print.info('compressing (level %d) %s -> %s' % (compressionLevel, filePath, nszPath))
	newNsp = Pfs0.Pfs0Stream(nszPath)

	try:
		for nspf in container:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
				Print.info('skipping delta fragment')
				continue
			if isinstance(nspf, Nca.Nca) and (nspf.header.contentType == Type.Content.PROGRAM or nspf.header.contentType == Type.Content.PUBLICDATA):
				if isNcaPacked(nspf, ncaHeaderSize):
					newFileName = nspf._path[0:-1] + 'z'
					f = newNsp.add(newFileName, nspf.size)
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

					for fs in sections:
						header += fs.offset.to_bytes(8, 'little')
						header += fs.size.to_bytes(8, 'little')
						header += fs.cryptoType.to_bytes(8, 'little')
						header += b'\x00' * 8
						header += fs.cryptoKey
						header += fs.cryptoCounter
					
					f.write(header)
					decompressedBytes = ncaHeaderSize

					with tqdm(total=nspf.size, unit_scale=True, unit="B") as bar:
						partitions = [nspf.partition(offset = section.offset, size = section.size, n = None, cryptoType = section.cryptoType, cryptoKey = section.cryptoKey, cryptoCounter = bytearray(section.cryptoCounter), autoOpen = True) for section in sections]
						partNr = 0
						bar.update(f.tell())
						cctx = ZstdCompressor(level=compressionLevel, threads=threads) if threads > 1 else ZstdCompressor(level=compressionLevel)
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
					newNsp.resize(newFileName, written)
					continue
				else:
					print('not packed!')
			f = newNsp.add(nspf._path, nspf.size)
			nspf.seek(0)
			while not nspf.eof():
				buffer = nspf.read(CHUNK_SZ)
				f.write(buffer)
	except KeyboardInterrupt:
		remove(nszPath)
		raise KeyboardInterrupt
	except BaseException:
		Print.error(format_exc())
		remove(nszPath)
	finally:
		newNsp.close()
		container.close()
	return nszPath