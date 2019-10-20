import multiprocessing
from nsz import BlockCompressor
from nsz import SolidCompressor
from nsz import NszDecompressor

def compress(filePath, compressionLevel = 18, useBlockCompression = False, blockSizeExponent = 20, outputDir = None, threads = -1, overwrite = False, verifyHash = False):
	if threads < 1:
		threads = multiprocessing.cpu_count()
	if useBlockCompression:
		outFile = BlockCompressor.blockCompress(filePath, compressionLevel, blockSizeExponent, threads, outputDir, overwrite)
	else:
		outFile = SolidCompressor.solidCompress(filePath, compressionLevel, outputDir, threads, overwrite)
	if verifyHash:
		print(outFile)
		verify(outFile, True)

def decompress(filePath, outputDir = None):
	NszDecompressor.decompress(filePath, outputDir)

def verify(filePath, raiseVerificationException):
	NszDecompressor.verify(filePath, raiseVerificationException)
