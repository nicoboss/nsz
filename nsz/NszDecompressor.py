from pathlib import Path
from traceback import format_exc
from hashlib import sha256
from nsz.nut import Print, aes128
from zstandard import ZstdDecompressor
from nsz.Fs import factory, Type, Pfs0, Hfs0, Nca, Xci
from nsz.PathTools import *
from nsz import Header, BlockDecompressorReader, FileExistingChecks
import os, enlighten

class VerificationException(Exception):
	pass

def decompress(filePath, outputDir, fixPadding, statusReportInfo, pleaseNoPrint = None):
	if isNspNsz(filePath):
		__decompressNsz(filePath, outputDir, fixPadding, True, False, False, statusReportInfo, None, pleaseNoPrint)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, outputDir, fixPadding, True, False, False, statusReportInfo, None, pleaseNoPrint)
	elif isCompressedGameFile(filePath):
		filePathNca = changeExtension(filePath, '.nca')
		outPath = filePathNca if outputDir == None else str(Path(outputDir).joinpath(Path(filePathNca).name))
		Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
		try:
			inFile = factory(filePath)
			inFile.open(str(filePath), 'rb')
			with open(outPath, 'wb') as outFile:
				written, hexHash = __decompressNcz(inFile, outFile, statusReportInfo, pleaseNoPrint)
				fileNameHash = Path(filePath).stem.lower()
				if hexHash[:32] == fileNameHash:
					Print.info('[VERIFIED]   {0}'.format(filePathNca), pleaseNoPrint)
				else:
					Print.info('[MISMATCH]   Filename startes with {0} but {1} was expected - hash verified failed!'.format(fileNameHash, hexHash[:32]), pleaseNoPrint)
		except BaseException as ex:
			if not ex is KeyboardInterrupt:
				Print.error(format_exc())
			if Path(outPath).is_file():
				Path(outPath).unlink()
		finally:
			inFile.close()
	else:
		raise NotImplementedError("Can't decompress {0} as that file format isn't implemented!".format(filePath))


def verify(filePath, fixPadding, raiseVerificationException, raisePfs0Exception, originalFilePath, statusReportInfo, pleaseNoPrint):
	if isNspNsz(filePath):
		__decompressNsz(filePath, None, fixPadding, False, raiseVerificationException, raisePfs0Exception, originalFilePath, statusReportInfo, pleaseNoPrint)
	elif isXciXcz(filePath):
		__decompressXcz(filePath, None, fixPadding, False, raiseVerificationException, raisePfs0Exception, originalFilePath, statusReportInfo, pleaseNoPrint)


def __decompressContainer(readContainer, writeContainer, fileHashes, write, raiseVerificationException, raisePfs0Exception, statusReportInfo, pleaseNoPrint):
	CHUNK_SZ = 0x100000
	if write:
		for nspf in readContainer:
			if not nspf._path.endswith('.ncz'):
				writeContainer.add(nspf._path, nspf.size, pleaseNoPrint)
			else:
				newFileName = Path(nspf._path).stem + '.nca'
				nca_size = __getDecompressedNczSize(nspf)
				writeContainer.add(newFileName, nca_size, pleaseNoPrint)
		writeContainer.updateHashHeader()
	for nspf in readContainer:
		Print.info('[EXISTS]     {0}'.format(nspf._path), pleaseNoPrint)
		if not nspf._path.endswith('.ncz'):
			verifyFile = nspf._path.endswith('.nca') and not nspf._path.endswith('.cnmt.nca')
			hash = sha256()
			nspf.seek(0)
			while not nspf.eof():
				inputChunk = nspf.read(CHUNK_SZ)
				hash.update(inputChunk)
				if write:
					writeContainer.get(nspf._path).write(inputChunk)
			if verifyFile:
				hashHexdigest = hash.hexdigest()
				if hasattr(nspf.f, 'ticketless'):
					# This ticket conditional was added to prevent the following exception from occurring when processing a ticketless dump file:
					# nut exception: Verification detected hash mismatch
					Print.info('[TICKETLESS] {0}'.format(nspf._path), pleaseNoPrint)
				else:
					if hashHexdigest in fileHashes:
						Print.info(f'[NCA HASH]   {hashHexdigest}', pleaseNoPrint)
						Print.info(f'[VERIFIED]   {nspf._path} {hashHexdigest}', pleaseNoPrint)
					else:
						Print.info(f'[NCA HASH]   {hashHexdigest}', pleaseNoPrint)
						Print.info(f'[CORRUPTED]  {nspf._path} {hashHexdigest}', pleaseNoPrint)
						if raiseVerificationException:
							raise VerificationException("Verification detected hash mismatch!")
			continue
		newFileName = Path(nspf._path).stem + '.nca'
		if write:
			written, hexHash = __decompressNcz(nspf, writeContainer.get(newFileName), statusReportInfo, pleaseNoPrint)
		else:
			written, hexHash = __decompressNcz(nspf, None, statusReportInfo, pleaseNoPrint)
		if hasattr(nspf.f, 'ticketless'):
			# This ticket conditional was added to prevent the following exception from occurring when processing a ticketless dump file:
			# nut exception: Verification detected hash mismatch
			Print.info('[TICKETLESS] {0}'.format(nspf._path), pleaseNoPrint)
		else:
			if hexHash in fileHashes:
				Print.info(f'[NCA HASH]   {hexHash}', pleaseNoPrint)
				Print.info(f'[VERIFIED]   {nspf._path}', pleaseNoPrint)
			else:
				Print.info(f'[NCA HASH]   {hexHash}', pleaseNoPrint)
				Print.info(f'[CORRUPTED]  {nspf._path}', pleaseNoPrint)
				if raiseVerificationException:
					raise VerificationException("Verification detected hash mismatch")


def __getDecompressedNczSize(nspf):
	UNCOMPRESSABLE_HEADER_SIZE = 0x4000
	nspf.seek(0)
	header = nspf.read(UNCOMPRESSABLE_HEADER_SIZE)
	magic = nspf.read(8)
	if not magic == b'NCZSECTN':
		raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
	sectionCount = nspf.readInt64()
	sections = [Header.Section(nspf) for _ in range(sectionCount)]
	if sections[0].offset-UNCOMPRESSABLE_HEADER_SIZE > 0:
		fakeSection = Header.FakeSection(UNCOMPRESSABLE_HEADER_SIZE, sections[0].offset-UNCOMPRESSABLE_HEADER_SIZE)
		sections.insert(0, fakeSection)
	nca_size = UNCOMPRESSABLE_HEADER_SIZE
	for i in range(sectionCount):
		nca_size += sections[i].size
	return nca_size


def __decompressNcz(nspf, f, statusReportInfo, pleaseNoPrint):
	UNCOMPRESSABLE_HEADER_SIZE = 0x4000
	blockID = 0
	nspf.seek(0)
	header = nspf.read(UNCOMPRESSABLE_HEADER_SIZE)
	currentStep = 'Decompress' if f != None else 'Verifying'
	if f != None:
		start = f.tell()
	magic = nspf.read(8)
	if not magic == b'NCZSECTN':
		raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
	sectionCount = nspf.readInt64()
	sections = [Header.Section(nspf) for _ in range(sectionCount)]
	if sections[0].offset-UNCOMPRESSABLE_HEADER_SIZE > 0:
		fakeSection = Header.FakeSection(UNCOMPRESSABLE_HEADER_SIZE, sections[0].offset-UNCOMPRESSABLE_HEADER_SIZE)
		sections.insert(0, fakeSection)
	nca_size = UNCOMPRESSABLE_HEADER_SIZE
	for i in range(sectionCount):
		nca_size += sections[i].size
	pos = nspf.tell()
	blockMagic = nspf.read(8)
	nspf.seek(pos)
	useBlockCompression = blockMagic == b'NCZBLOCK'
	blockSize = -1
	if useBlockCompression:
		Print.info(f'[NCZBLOCK]   Using Block decompression for {nspf._path}')
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
	decompressedBytesOld = decompressedBytes
	if f != None:
		f.write(header)
	if statusReportInfo != None:
		statusReport, id = statusReportInfo
		statusReport[id] = [len(header), 0, nca_size, currentStep]
	else:
		bar.count = decompressedBytes//1048576
		bar.refresh()
	hash.update(header)

	firstSection = True
	for s in sections:
		i = s.offset
		useCrypto = s.cryptoType in (3, 4)
		if useCrypto:
			crypto = aes128.AESCTR(s.cryptoKey, s.cryptoCounter)
		end = s.offset + s.size
		if firstSection:
			firstSection = False
			uncompressedSize = UNCOMPRESSABLE_HEADER_SIZE-sections[0].offset
			if uncompressedSize > 0:
				i += uncompressedSize
		while i < end:
			if useCrypto:
				crypto.seek(i)
			chunkSz = 0x10000 if end - i > 0x10000 else end - i
			if useBlockCompression:
				inputChunk = blockDecompressorReader.read(chunkSz)
			else:
				inputChunk = decompressor.read(chunkSz)
			if not len(inputChunk):
				break
			if useCrypto:
				inputChunk = crypto.encrypt(inputChunk)
			if f != None:
				f.write(inputChunk)
			hash.update(inputChunk)
			lenInputChunk = len(inputChunk)
			i += lenInputChunk
			decompressedBytes += lenInputChunk
			if statusReportInfo != None:
				statusReport[id] = [statusReport[id][0]+chunkSz, statusReport[id][1], nca_size, currentStep]
			elif decompressedBytes - decompressedBytesOld > 52428800: #Refresh every 50 MB
				decompressedBytesOld = decompressedBytes
				bar.count = decompressedBytes//1048576
				bar.refresh()

	if statusReportInfo == None:
		bar.count = decompressedBytes//1048576
		bar.close()
		#Line break after closing the process bar is required to prevent
		#the next output from being on the same line as the process bar
		print()
	hexHash = hash.hexdigest()
	if f != None:
		end = f.tell()
		written = (end - start)
		return (written, hexHash)
	return (0, hexHash)


def __decompressNsz(filePath, outputDir, fixPadding, write, raiseVerificationException, raisePfs0Exception, originalFilePath, statusReportInfo, pleaseNoPrint):
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	fileHashes = FileExistingChecks.ExtractHashes(container)
	
	try:
		if write:
			filePathNsp = changeExtension(filePath, '.nsp')
			outPath = filePathNsp if outputDir == None else str(Path(outputDir).joinpath(Path(filePathNsp).name))
			Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
			with Pfs0.Pfs0Stream(container.getPaddedHeaderSize() if fixPadding else container.getFirstFileOffset(), None if fixPadding else container.getStringTableSize(), outPath) as nsp:
				__decompressContainer(container, nsp, fileHashes, True, raiseVerificationException, raisePfs0Exception, statusReportInfo, pleaseNoPrint)
		else:
			with Pfs0.Pfs0VerifyStream(container.getPaddedHeaderSize() if fixPadding else container.getFirstFileOffset(), None if fixPadding else container.getStringTableSize()) as nsp:
				__decompressContainer(container, nsp, fileHashes, True, raiseVerificationException, raisePfs0Exception, statusReportInfo, pleaseNoPrint)
				Print.info("[NSP SHA256] " + nsp.getHash())
				if originalFilePath != None: 
					originalContainer = factory(originalFilePath)
					CHUNK_SZ = 0x100000
					originalHash = sha256()
					filesize = os.path.getsize(str(originalFilePath))
					if statusReportInfo == None:
						BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
						bar = enlighten.Counter(total=filesize//CHUNK_SZ, desc='Verifying', unit="MiB", color='yellow', bar_format=BAR_FMT)
					blockCount = 0
					with open(str(originalFilePath), 'rb') as f:
						while True:
							data = f.read(CHUNK_SZ)
							blockCount += 1
							if statusReportInfo != None:
								statusReport, id = statusReportInfo
								statusReport[id] = [blockCount, 0, filesize, 'Verifying']
							else:
								bar.count = blockCount
								bar.refresh()
							if not data:
								break
							originalHash.update(data)
					originalHashHex = originalHash.hexdigest()
					if statusReportInfo == None:
						bar.close()
					Print.info("[NSP SHA256] " + originalHashHex)
					if nsp.getHash() == originalHashHex:
						Print.info("[VERIFIED]   NSP SHA256")
					else:
						Print.info("[MISSMATCH]  NSP SHA256")
						if raisePfs0Exception:
							raise VerificationException("Verification detected NSP SHA256 hash mismatch!")
	except BaseException:
		raise
	finally:
		container.close()


def __decompressXcz(filePath, outputDir, fixPadding, write, raiseVerificationException, raisePfs0Exception, originalFilePath, statusReportInfo, pleaseNoPrint):
	container = factory(filePath)
	container.open(str(filePath), 'rb')
	
	if write:
		filePathXci = changeExtension(filePath, '.xci')
		outPath = filePathXci if outputDir == None else str(Path(outputDir).joinpath(Path(filePathXci).name))
		Print.info('Decompressing %s -> %s' % (filePath, outPath), pleaseNoPrint)
		with Xci.XciStream(outPath, originalXciPath = filePath) as xci: # need filepath to copy XCI container settings
			for partitionIn in container.hfs0:
				fileHashes = FileExistingChecks.ExtractHashes(partitionIn)
				hfsPartitionIn = xci.hfs0.add(partitionIn._path, 0x200, pleaseNoPrint)
				with Hfs0.Hfs0Stream(hfsPartitionIn, xci.f.tell()) as partitionOut:
					__decompressContainer(partitionIn, partitionOut, fileHashes, write, raiseVerificationException, raisePfs0Exception, statusReportInfo, pleaseNoPrint)
				xci.hfs0.resize(partitionIn._path, partitionOut.actualSize)
	else:
		for partitionIn in container.hfs0:
			fileHashes = FileExistingChecks.ExtractHashes(partitionIn)
			__decompressContainer(partitionIn, None, fileHashes, write, raiseVerificationException, raisePfs0Exception, statusReportInfo, pleaseNoPrint)

	container.close()
