from nsz import BlockCompressor
from nsz import SolidCompressor
from nsz import NszDecompressor

def compress(filePath, compressionLevel = 18, useBlockCompression = False, blockSizeExponent = 20, outputDir = None, threads = -1, overwrite = False):
	if threads == -1:
		threads = multiprocessing.cpu_count()
	if useBlockCompression:
		BlockCompressor.blockCompress(filePath, compressionLevel, blockSizeExponent, outputDir, threads, overwrite)
	else:
		SolidCompressor.solidCompress(filePath, compressionLevel, outputDir, threads, overwrite)


def decompress(filePath, outputDir = None):
	NszDecompressor.decompress(filePath, outputDir)
