from pathlib import Path
from hashlib import sha256
from nut import Print, aes128
from zstandard import ZstdDecompressor
from Fs import factory, Type, Pfs0, Hfs0, Nca, Xci
from PathTools import *
import Header, BlockDecompressorReader, FileExistingChecks
import enlighten

def decompress(filePath, outputDir = None):
	if filePath.endswith('.nsz'):
		__decompressNsz(filePath, outputDir, True, False)
	elif filePath.endswith('.xcz'):
		__decompressXcz(filePath, outputDir, True, False)
	elif filePath.endswith('.ncz'):
		filename = changeExtension(filePath, '.nca')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath))
		container = factory(filePath)
		container.open(filePath, 'rb')
		try:
			with open(outPath, 'wb') as outFile:
				written, hexHash = __decompressNcz(container, outFile)
		except BaseException as ex:
			if not ex is KeyboardInterrupt:
				Print.error(format_exc())
			if outFile.is_file():
				outFile.unlink()
		finally:
			container.close()
		fileNameHash = Path(filePath).stem.lower()
		if hexHash[:32] == fileNameHash:
			Print.error('[VERIFIED]   {0}'.format(filename))
		else:
			Print.info('[MISMATCH]   Filename startes with {0} but {1} was expected - hash verified failed!'.format(fileNameHash, hexHash[:32]))
	else:
		raise NotImplementedError("Can't decompress {0} as that file format isn't implemented!".format(filePath))


def verify(filePath, raiseVerificationException):
	if isNspNsz(filePath):
		__decompressNsz(filePath, None, False, raiseVerificationException)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, None, False, raiseVerificationException)


def __decompressContainer(readContainer, writeContainer, fileHashes, write = True, raiseVerificationException = False):
	for nspf in readContainer:
		CHUNK_SZ = 0x100000
		f = None
		if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
			Print.info('skipping delta fragment')
			continue
		if not nspf._path.endswith('.ncz'):
			verifyFile = nspf._path.endswith('.nca') and not nspf._path.endswith('.cnmt.nca')
			if write:
				f = writeContainer.add(nspf._path, nspf.size)
			hash = sha256()
			nspf.seek(0)
			while not nspf.eof():
				inputChunk = nspf.read(CHUNK_SZ)
				hash.update(inputChunk)
				if write:
					f.write(inputChunk)
			if verifyFile:
				if hash.hexdigest() in fileHashes:
					Print.error('[VERIFIED]   {0}'.format(nspf._path))
				else:
					Print.info('[CORRUPTED]  {0}'.format(nspf._path))
					if raiseVerificationException:
						raise Exception("Verification detected hash missmatch!")
			elif not write:
				Print.info('[EXISTS]     {0}'.format(nspf._path))
			continue
		newFileName = Path(nspf._path).stem + '.nca'
		if write:
			f = writeContainer.add(newFileName, nspf.size)
		written, hexHash = __decompressNcz(nspf, f)
		if write:
			writeContainer.resize(newFileName, written)
		if hexHash in fileHashes:
			Print.error('[VERIFIED]   {0}'.format(nspf._path))
		else:
			Print.info('[CORRUPTED]  {0}'.format(nspf._path))
			if raiseVerificationException:
				raise Exception("Verification detected hash missmatch")


def __decompressNcz(nspf, f):
	ncaHeaderSize = 0x4000
	blockID = 0
	nspf.seek(0)
	header = nspf.read(ncaHeaderSize)
	if f != None:
		start = f.tell()

	magic = nspf.read(8)
	if not magic == b'NCZSECTN':
		raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
	sectionCount = nspf.readInt64()
	sections = [Header.Section(nspf) for _ in range(sectionCount)]
	nca_size = ncaHeaderSize
	for i in range(sectionCount):
		nca_size += sections[i].size
	pos = nspf.tell()
	blockMagic = nspf.read(8)
	nspf.seek(pos)
	useBlockCompression = blockMagic == b'NCZBLOCK'
	blockSize = -1
	if useBlockCompression:
		BlockHeader = Header.Block(nspf)
		blockDecompressorReader = BlockDecompressorReader.BlockDecompressorReader(nspf, BlockHeader)
	pos = nspf.tell()
	if not useBlockCompression:
		decompressor = ZstdDecompressor().stream_reader(nspf)
	hash = sha256()
	with enlighten.Counter(total=nca_size, unit="B") as bar:
		if f != None:
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
				if f != None:
					f.write(inputChunk)
				hash.update(inputChunk)
				i += len(inputChunk)
				bar.update(chunkSz)

	hexHash = hash.hexdigest()
	if f != None:
		end = f.tell()
		written = (end - start)
		return (written, hexHash)
	return (0, hexHash)


def __decompressNsz(filePath, outputDir = None, write = True, raiseVerificationException = False):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	
	if write:
		filename = changeExtension(filePath, '.nsp')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath))
		with Pfs0.Pfs0Stream(outPath) as nsp:
			__decompressContainer(container, nsp, fileHashes, write, raiseVerificationException)
	else:
		__decompressContainer(container, None, fileHashes, write, raiseVerificationException)

	container.close()


def __decompressXcz(filePath, outputDir = None, write = True, raiseVerificationException = False):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	container = factory(filePath)
	container.open(filePath, 'rb')
	secureIn = container.hfs0['secure']
	
	if write:
		filename = changeExtension(filePath, '.xci')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath))
		with Xci.XciStream(outPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0), xci.f.tell()) as secureOut:
				__decompressContainer(secureIn, secureOut, fileHashes, write, raiseVerificationException)
				xci.hfs0.resize('secure', secureOut.actualSize)
	else:
		__decompressContainer(secureIn, None, fileHashes, write, raiseVerificationException)

	container.close()

