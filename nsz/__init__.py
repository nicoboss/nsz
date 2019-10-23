import multiprocessing
from nsz import BlockCompressor
from nsz import SolidCompressor
from nsz import NszDecompressor

def compress(filePath, args, filesAtTarget):
	compressionLevel = 18 if args.level is None else args.level
	if args.threads < 1:
		threads = multiprocessing.cpu_count()
	if args.block:
		outFile = BlockCompressor.blockCompress(filePath, compressionLevel, args.bs)
	else:
		outFile = SolidCompressor.solidCompress(filePath, compressionLevel, args.output, args.threads if args.enable_solid_multithreading else -1, args.overwrite, filesAtTarget)
	if args.verify:
		print("[VERIFY NSZ] {0}".format(outFile))
		verify(outFile, True)

def decompress(filePath, outputDir = None):
	NszDecompressor.decompress(filePath, outputDir)

def verify(filePath, raiseVerificationException):
	NszDecompressor.verify(filePath, raiseVerificationException)
