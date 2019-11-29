from tqdm import tqdm
from pathlib import Path
from hashlib import sha256
from nut import Print, aes128
from zstandard import ZstdDecompressor
from Fs import factory, Type, Pfs0, Hfs0, Nca, Xci
from GameType import *
import Header, BlockDecompressorReader, FileExistingChecks

def decompress(filePath, outputDir = None):
	if filePath.endswith('.nsz'):
		__decompressNsz(filePath, outputDir, True, False)
	elif filePath.endswith('.xcz'):
		__decompressXcz(filePath, outputDir, True, False)

def verify(filePath, raiseVerificationException):
	if isNspNsz(filePath):
		__decompressNsz(filePath, None, False, raiseVerificationException)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, None, False, raiseVerificationException)

def __decompressContainer(readContainer, writeContainer, fileHashes, write = True, raiseVerificationException = False):
	ncaHeaderSize = 0x4000
	CHUNK_SZ = 0x100000
	for nspf in readContainer:
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
		newFileName = getBasename(nspf._path) + '.nca'
		if write:
			f = writeContainer.add(newFileName, nspf.size)
			start = f.tell()
		blockID = 0
		nspf.seek(0)
		header = nspf.read(ncaHeaderSize)

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
		with tqdm(total=nca_size, unit_scale=True, unit="B") as bar:
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
					hash.update(inputChunk)
					i += len(inputChunk)
					bar.update(chunkSz)

		if hash.hexdigest() in fileHashes:
			Print.error('[VERIFIED]   {0}'.format(nspf._path))
		else:
			Print.info('[CORRUPTED]  {0}'.format(nspf._path))
			if raiseVerificationException:
				raise Exception("Verification detected hash missmatch")
		if write:
			end = f.tell()
			written = (end - start)
			writeContainer.resize(newFileName, written)
		continue
		


def __decompressNsz(filePath, outputDir = None, write = True, raiseVerificationException = False):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	
	if write:
		filename = changeExtension(filePath, '.nsp')
		outPath = str(filename) if outputDir == None else Path(outputDir).joinpath(filename).name.resolve(strict=False)
		Print.info('decompressing %s -> %s' % (filePath, outPath))
		with Pfs0.Pfs0Stream(outPath) as nsp:
			__decompressContainer(container, nsp, fileHashes, write, raiseVerificationException)
	else:
		__decompressContainer(container, None, fileHashes, write, raiseVerificationException)

	container.close()


def __decompressXcz(filePath, outputDir = None, write = True, raiseVerificationException = False):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	filePath = str(Path(filePath).resolve())
	container = factory(filePath)
	container.open(filePath, 'rb')
	secureIn = container.hfs0['secure']
	
	if write:
		filename = changeExtension(filePath, '.xci')
		outPath = str(filename) if outputDir == None else Path(outputDir).joinpath(filename).name.resolve(strict=False)
		Print.info('decompressing %s -> %s' % (filePath, outPath))
		with Xci.XciStream(outPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0), xci.f.tell()) as secureOut:
				__decompressContainer(secureIn, secureOut, fileHashes, write, raiseVerificationException)
				xci.hfs0.resize('secure', secureOut.actualSize)
	else:
		__decompressContainer(secureIn, None, fileHashes, write, raiseVerificationException)

	container.close()

