from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from nsz.Fs.File import File
from hashlib import sha256
import os
import re
import pathlib
from nsz.nut import Keys
from nsz.nut import Print

MEDIA_SIZE = 0x200


class IvfcLevel:
	def __init__(self, offset, size, blockSize, reserved):
		self.offset = offset
		self.size = size
		self.blockSize = blockSize
		self.reserved = reserved

class Ivfc(File):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		self.magic = None
		self.magicNumber = None
		self.masterHashSize = None
		self.numberLevels = None
		self.levels = []
		self.hash = None
		super(Ivfc, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)

	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Ivfc, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		self.magic = self.read(0x4)
		self.magicNumber = self.readInt32()
		self.masterHashSize = self.readInt32()
		self.numberLevels = self.readInt32()

		for i in range(self.numberLevels-1):
			self.levels.append(IvfcLevel(self.readInt64(), self.readInt64(), self.readInt32(), self.readInt32()))

		self.read(32)
		self.hash = self.read(32)
		