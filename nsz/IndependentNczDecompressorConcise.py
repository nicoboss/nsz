#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import argv
from pathlib import Path
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util import Counter
from zstandard import ZstdDecompressor


def readInt8(f, byteorder="little", signed=False):
	return int.from_bytes(f.read(1), byteorder=byteorder, signed=signed)


def readInt32(f, byteorder="little", signed=False):
	return int.from_bytes(f.read(4), byteorder=byteorder, signed=signed)


def readInt64(f, byteorder="little", signed=False):
	return int.from_bytes(f.read(8), byteorder=byteorder, signed=signed)


class AESCTR:
	def __init__(self, key, nonce, offset=0):
		self.key = key
		self.nonce = nonce
		self.seek(offset)

	def encrypt(self, data):
		return self.aes.encrypt(data)

	def seek(self, offset):
		self.ctr = Counter.new(64, prefix=self.nonce[0:8], initial_value=(offset >> 4))
		self.aes = AES.new(self.key, AES.MODE_CTR, counter=self.ctr)


class Section:
	def __init__(self, f):
		self.f = f
		self.offset = readInt64(f)
		self.size = readInt64(f)
		self.cryptoType = readInt64(f)
		readInt64(f)  # padding
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
	nca_header_size = 0x4000
	nspf.seek(0)
	header = nspf.read(nca_header_size)
	assert nspf.read(8) == b"NCZSECTN"
	section_count = readInt64(nspf)
	sections = [Section(nspf) for _ in range(section_count)]
	pos = nspf.tell()
	useBlockCompression = nspf.read(8) == b'NCZBLOCK'
	nspf.seek(pos)
	if useBlockCompression:
		block_header = Block(nspf)
	else:
		decompressor = ZstdDecompressor().stream_reader(nspf)
	hash = sha256()
	f.write(header)
	hash.update(header)

	if useBlockCompression:
		pos = sections[0].offset
		section_id = 0
		s = sections[section_id]
		block_size = 1 << block_header.blockSizeExponent
		for block_i in range(block_header.numberOfBlocks):
			data = nspf.read(block_header.compressedBlockSizeList[block_i])
			if len(data) < block_size:
				data = ZstdDecompressor().decompress(data)
			end = pos + len(data)
			while pos < end:
				if pos >= s.offset + s.size:
					section_id += 1
					s = sections[section_id]
				part_size = min(end, s.offset + s.size) - pos
				part, data = data[:part_size], data[part_size:]
				if s.cryptoType in (3, 4):
					crypto = AESCTR(s.cryptoKey, s.cryptoCounter, pos)
					part = crypto.encrypt(part)
				f.write(part)
				hash.update(part)
				pos += part_size
	else:
		for s in sections:
			i = s.offset
			crypto = AESCTR(s.cryptoKey, s.cryptoCounter)
			end = s.offset + s.size
			while i < end:
				crypto.seek(i)
				chunkSz = 0x400000 if end - i > 0x400000 else end - i
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
	return hexHash


if __name__ == "__main__":
	if len(argv) < 3:
		print("usage: decompress.py input.ncz output.nca")
		exit(1)
	hexHash = __decompressNcz(open(argv[1], "rb"), open(argv[2], "wb"))
	fileNameHash = Path(argv[1]).stem.lower()
	if hexHash[:32] == fileNameHash:
		print('[VERIFIED]   {0}'.format(Path(argv[2]).name))
	else:
		print('[MISMATCH]   Filename startes with {0} but {1} was expected - hash verified failed!'.format(fileNameHash, hexHash[:32]))
	print("Done!")
