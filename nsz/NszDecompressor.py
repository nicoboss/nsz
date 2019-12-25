from pathlib import Path
from hashlib import sha256
from nut import Print, aes128
from zstandard import ZstdDecompressor
from Fs import factory, Type, Pfs0, Hfs0, Nca, Xci
from PathTools import *
import Header, BlockDecompressorReader, FileExistingChecks
import enlighten


def decompress(filePath, outputDir, statusReportInfo, pleaseNoPrint = None):
	if isNspNsz(filePath):
		__decompressNsz(filePath, outputDir, True, False, statusReportInfo, pleaseNoPrint)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, outputDir, True, False, statusReportInfo, pleaseNoPrint)
	elif isCompressedGameFile(filePath):
		filename = changeExtension(filePath, '.nca')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
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
			Print.info('[VERIFIED]   {0}'.format(filename), pleaseNoPrint)
		else:
			Print.info('[MISMATCH]   Filename startes with {0} but {1} was expected - hash verified failed!'.format(fileNameHash, hexHash[:32]), pleaseNoPrint)
	else:
		raise NotImplementedError("Can't decompress {0} as that file format isn't implemented!".format(filePath))


def verify(filePath, raiseVerificationException, statusReportInfo, pleaseNoPrint):
	if isNspNsz(filePath):
		__decompressNsz(filePath, None, False, raiseVerificationException, statusReportInfo, pleaseNoPrint)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, None, False, raiseVerificationException, statusReportInfo, pleaseNoPrint)


def __decompressContainer(readContainer, writeContainer, fileHashes, write, raiseVerificationException, statusReportInfo, pleaseNoPrint):
	for nspf in readContainer:
		CHUNK_SZ = 0x100000
		f = None
		if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.DATA:
			Print.info('skipping delta fragment', pleaseNoPrint)
			continue
		if not nspf._path.endswith('.ncz'):
			verifyFile = nspf._path.endswith('.nca') and not nspf._path.endswith('.cnmt.nca')
			if write:
				f = writeContainer.add(nspf._path, nspf.size, pleaseNoPrint)
			hash = sha256()
			nspf.seek(0)
			while not nspf.eof():
				inputChunk = nspf.read(CHUNK_SZ)
				hash.update(inputChunk)
				if write:
					f.write(inputChunk)
			if verifyFile:
				if hash.hexdigest() in fileHashes:
					Print.info('[VERIFIED]   {0}'.format(nspf._path), pleaseNoPrint)
				else:
					Print.info('[CORRUPTED]  {0}'.format(nspf._path), pleaseNoPrint)
					if raiseVerificationException:
						raise Exception("Verification detected hash missmatch!")
			elif not write:
				Print.info('[EXISTS]     {0}'.format(nspf._path), pleaseNoPrint)
			continue
		newFileName = Path(nspf._path).stem + '.nca'
		if write:
			f = writeContainer.add(newFileName, nspf.size, pleaseNoPrint)
		written, hexHash = __decompressNcz(nspf, f, statusReportInfo, pleaseNoPrint)
		if write:
			writeContainer.resize(newFileName, written)
		if hexHash in fileHashes:
			Print.info('[VERIFIED]   {0}'.format(nspf._path), pleaseNoPrint)
		else:
			Print.info('[CORRUPTED]  {0}'.format(nspf._path), pleaseNoPrint)
			if raiseVerificationException:
				raise Exception("Verification detected hash missmatch")


def __decompressNcz(nspf, f, statusReportInfo, pleaseNoPrint):
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
	
	if statusReportInfo == None:
		BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
		bar = enlighten.Counter(total=nca_size//1048576, desc='Decompress', unit="MiB", color='red', bar_format=BAR_FMT)
	decompressedBytes = len(header)
	if f != None:
		f.write(header)
	if statusReportInfo != None:
		statusReport, id = statusReportInfo
		statusReport[id] = [len(header), 0, nca_size]
	else:
		bar.count = decompressedBytes//1048576
		bar.refresh()
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
			lenInputChunk = len(inputChunk)
			i += lenInputChunk
			decompressedBytes += lenInputChunk
			if statusReportInfo != None:
				statusReport[id] = [statusReport[id][0]+chunkSz, statusReport[id][1], nca_size]
			else:
				bar.count = decompressedBytes//1048576
				bar.refresh()

	bar.close()
	hexHash = hash.hexdigest()
	if f != None:
		end = f.tell()
		written = (end - start)
		return (written, hexHash)
	return (0, hexHash)


def __decompressNsz(filePath, outputDir, write, raiseVerificationException, statusReportInfo, pleaseNoPrint):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	
	if write:
		filename = changeExtension(filePath, '.nsp')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
		with Pfs0.Pfs0Stream(outPath) as nsp:
			__decompressContainer(container, nsp, fileHashes, write, raiseVerificationException, statusReportInfo, pleaseNoPrint)
	else:
		__decompressContainer(container, None, fileHashes, write, raiseVerificationException, statusReportInfo, pleaseNoPrint)

	container.close()


def __decompressXcz(filePath, outputDir, write, raiseVerificationException, statusReportInfo, pleaseNoPrint):
	fileHashes = FileExistingChecks.ExtractHashes(filePath)
	container = factory(filePath)
	container.open(filePath, 'rb')
	secureIn = container.hfs0['secure']
	
	if write:
		filename = changeExtension(filePath, '.xci')
		outPath = filename if outputDir == None else str(Path(outputDir).joinpath(filename))
		Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
		with Xci.XciStream(outPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			with Hfs0.Hfs0Stream(xci.hfs0.add('secure', 0, pleaseNoPrint), xci.f.tell()) as secureOut:
				__decompressContainer(secureIn, secureOut, fileHashes, write, raiseVerificationException, statusReportInfo, pleaseNoPrint)
				xci.hfs0.resize('secure', secureOut.actualSize)
	else:
		__decompressContainer(secureIn, None, fileHashes, write, raiseVerificationException, statusReportInfo, pleaseNoPrint)

	container.close()

