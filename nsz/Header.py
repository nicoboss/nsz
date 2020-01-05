class Section:
	def __init__(self, f):
		self.f = f
		self.offset = f.readInt64()
		self.size = f.readInt64()
		self.cryptoType = f.readInt64()
		f.readInt64() # padding
		self.cryptoKey = f.read(16)
		self.cryptoCounter = f.read(16)

class FakeSection:
	def __init__(self, offset, size):
		self.offset = offset
		self.size = size
		self.cryptoType = 1

class Block:
	def __init__(self, f):
		self.f = f
		self.magic = f.read(8)
		self.version = f.readInt8()
		self.type = f.readInt8()
		self.unused = f.readInt8()
		self.blockSizeExponent = f.readInt8()
		self.numberOfBlocks = f.readInt32()
		self.decompressedSize = f.readInt64()
		self.compressedBlockSizeList = [f.readInt32() for _ in range(self.numberOfBlocks)]