from zstandard import ZstdDecompressor

class BlockDecompressorReader:
	#Position in decompressed data
	Position = 0
	BlockHeader = None
	CurrentBlock = b""
	CurrentBlockId = -1

	def __init__(self, nspf, BlockHeader):
		self.BlockHeader = BlockHeader
		initialOffset = nspf.tell()
		self.nspf = nspf
		if BlockHeader.blockSizeExponent < 14 or BlockHeader.blockSizeExponent > 32:
			raise ValueError("Corrupted NCZBLOCK header: Block size must be between 14 and 32")
		self.BlockSize = 2**BlockHeader.blockSizeExponent
		self.CompressedBlockOffsetList = [initialOffset]

		for compressedBlockSize in BlockHeader.compressedBlockSizeList[:-1]:
			self.CompressedBlockOffsetList.append(self.CompressedBlockOffsetList[-1] + compressedBlockSize)

		self.CompressedBlockSizeList = BlockHeader.compressedBlockSizeList

	def __decompressBlock(self, blockID):
		if self.CurrentBlockId == blockID:
			return self.CurrentBlock
		decompressedBlockSize = self.BlockSize
		if blockID >= len(self.CompressedBlockOffsetList) - 1:
			if blockID >= len(self.CompressedBlockOffsetList):
				raise EOFError("BlockID exceeds the amounts of compressed blocks in that file!")
			remainder = self.BlockHeader.decompressedSize % self.BlockSize
			# https://github.com/nicoboss/nsz/issues/210
			if remainder > 0:
				decompressedBlockSize = remainder
		self.nspf.seek(self.CompressedBlockOffsetList[blockID])
		if self.CompressedBlockSizeList[blockID] < decompressedBlockSize:
			self.CurrentBlock = ZstdDecompressor().decompress(self.nspf.read(self.CompressedBlockSizeList[blockID]))
		else:
			self.CurrentBlock = self.nspf.read(decompressedBlockSize)
		self.CurrentBlockId = blockID
		return self.CurrentBlock

	def seek(self, offset, whence = 0):
		if whence == 0:
			self.Position = offset
		elif whence == 1:
			self.Position += offset
		elif whence == 2:
			self.Position = self.BlockHeader.decompressedSize + offset
		else:
			raise ValueError("whence argument must be 0, 1 or 2")

	def read(self, length):
		buffer = b""
		blockOffset = self.Position%self.BlockSize
		blockID = self.Position//self.BlockSize

		while(len(buffer) - blockOffset < length):
			if blockID >= len(self.CompressedBlockOffsetList):
				break

			buffer += self.__decompressBlock(blockID)
			blockID += 1

		buffer = buffer[blockOffset:blockOffset+length]
		self.Position += length

		return buffer
