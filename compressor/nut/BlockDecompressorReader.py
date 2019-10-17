import zstandard

class BlockDecompressorReader:
	
	#Position in decompressed data
	Position = 0
	
	def __init__(self, nspf, BlockHeader):
		initialOffset = nspf.tell()
		self.nspf = nspf
		self.dctx = zstandard.ZstdDecompressor()
		if BlockHeader.blockSizeExponent < 14 or BlockHeader.blockSizeExponent > 32:
			raise ValueError("Corrupted NCZBLOCK header: Block size must be between 14 and 32")
		self.BlockSize = 2**BlockHeader.blockSizeExponent
		compressedBlockOffsetList = []
		compressedBlockOffsetList.append(initialOffset)
		for compressedBlockSize in BlockHeader.compressedBlockSizeList:
			compressedBlockOffsetList.append(compressedBlockOffsetList[-1]+compressedBlockSize)
		self.CompressedBlockOffsetList = compressedBlockOffsetList
		
	
	def __decompressBlock(self, blockID):
		if(blockID >= len(self.CompressedBlockOffsetList)):
			raise EOFError("BlockID exceeds the amounts of compressed blocks in that file!")
		self.nspf.seek(self.CompressedBlockOffsetList[blockID])
		decompressor = self.dctx.stream_reader(self.nspf)
		inputChunk = decompressor.read(self.BlockSize)
		decompressor.flush()
		#print('Block', str(blockID+1)+'/'+str(len(self.CompressedBlockOffsetList)))
		return inputChunk
	
	
	def seek(self, offset, whence = 0):
		if whence == 0:
			self.Position = offset
		elif whence  == 1:
			self.Position += offset
		elif whence  == 2:
			self.Position = decompressedSize - offset
		else:
			raise ValueError("whence argument must be 0, 1 or 2")
	
	
	def read(self, length):
		buffer = b""
		while(len(buffer) < length):
			blockID = self.Position//self.BlockSize
			blockOffset = self.Position%self.BlockSize
			if blockID >= len(self.CompressedBlockOffsetList):
				break
			newData = self.__decompressBlock(blockID)[blockOffset:blockOffset+length]
			self.Position += len(newData)
			buffer += newData
			blockID += 1
		return buffer
