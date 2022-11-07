#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import argv
from pathlib import Path
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util import Counter
from binascii import hexlify as hx
from zstandard import ZstdDecompressor

if len(argv) < 3:
	print('usage: decompress.py input.ncz output.nca')

def readInt8(f, byteorder='little', signed = False):
	return int.from_bytes(f.read(1), byteorder=byteorder, signed=signed)

def readInt32(f, byteorder='little', signed = False):
	return int.from_bytes(f.read(4), byteorder=byteorder, signed=signed)

def readInt64(f, byteorder='little', signed = False):
	return int.from_bytes(f.read(8), byteorder=byteorder, signed=signed)

def readInt128(f, byteorder='little', signed = False):
	return int.from_bytes(f.read(16), byteorder=byteorder, signed=signed)

class AESCTR:
	def __init__(self, key, nonce, offset = 0):
		self.key = key
		self.nonce = nonce
		self.seek(offset)

	def encrypt(self, data, ctr=None):
		if ctr is None:
			ctr = self.ctr
		return self.aes.encrypt(data)

	def decrypt(self, data, ctr=None):
		return self.encrypt(data, ctr)

	def seek(self, offset):
		self.ctr = Counter.new(64, prefix=self.nonce[0:8], initial_value=(offset >> 4))
		self.aes = AES.new(self.key, AES.MODE_CTR, counter=self.ctr)

class Section:
	def __init__(self, f):
		self.f = f
		self.offset = readInt64(f)
		self.size = readInt64(f)
		self.cryptoType = readInt64(f)
		readInt64(f) # padding
		self.cryptoKey = f.read(16)
		self.cryptoCounter = f.read(16)

class Block:
	def __init__(self, f):
		self.f = f
		self.magic = f.read(8)
		self.version = readInt8(f)
		self.type = readInt8(f)
		self.unused = readInt8(f)
		self.blockSizeExponent = readInt8(f)
		self.numberOfBlocks = readInt32(f)
		self.decompressedSize = readInt64(f)
		self.compressedBlockSizeList = [readInt32(f) for _ in range(self.numberOfBlocks)]
		

def __decompressNcz(nspf, f):
	ncaHeaderSize = 0x4000
	blockID = 0
	nspf.seek(0)
	header = nspf.read(ncaHeaderSize)
	start = f.tell()

	magic = nspf.read(8)
	if not magic == b'NCZSECTN':
		raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
	sectionCount = readInt64(nspf)
	sections = [Section(nspf) for _ in range(sectionCount)]
	nca_size = ncaHeaderSize
	for i in range(sectionCount):
		nca_size += sections[i].size
	pos = nspf.tell()
	blockMagic = nspf.read(8)
	nspf.seek(pos)
	useBlockCompression = blockMagic == b'NCZBLOCK'
	blockSize = -1
	if useBlockCompression:
		BlockHeader = Block(nspf)
		blockDecompressorReader = BlockDecompressorReader.BlockDecompressorReader(nspf, BlockHeader)
	pos = nspf.tell()
	if not useBlockCompression:
		decompressor = ZstdDecompressor().stream_reader(nspf)
	hash = sha256()
	f.write(header)
	hash.update(header)

	for s in sections:
		i = s.offset
		crypto = AESCTR(s.cryptoKey, s.cryptoCounter)
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
			if s.cryptoType in (3, 4):
				inputChunk = crypto.encrypt(inputChunk)
			f.write(inputChunk)
			hash.update(inputChunk)
			i += len(inputChunk)

	hexHash = hash.hexdigest()
	end = f.tell()
	written = (end - start)
	return (written, hexHash)


if __name__ == '__main__':
	with open(argv[1], 'rb') as nspf:
		with open(argv[2], 'wb+') as f:
			written, hexHash = __decompressNcz(nspf, f)
			fileNameHash = Path(argv[1]).stem.lower()
			if hexHash[:32] == fileNameHash:
				print('[VERIFIED]   {0}'.format(Path(argv[2]).name))
			else:
				print('[MISMATCH]   Filename startes with {0} but {1} was expected - hash verified failed!'.format(fileNameHash, hexHash[:32]))
	print("Done!")
