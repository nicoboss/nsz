from nut import BlockCompressor
from nut import SolidCompressor
from nut import Decompressor

def compress(filePath, compressionLevel = 17, useBlockCompression = False, blockSizeExponent = 19, outputDir = None, threads = -1):
	if threads == -1:
		threads = multiprocessing.cpu_count()
	if useBlockCompression:
		BlockCompressor.blockCompress(filePath, compressionLevel, blockSizeExponent, outputDir, threads)
	else:
		SolidCompressor.solidCompress(filePath, compressionLevel, outputDir, threads)


def decompress(filePath, outputDir = None):
	Decompressor.decompress(filePath, outputDir)
