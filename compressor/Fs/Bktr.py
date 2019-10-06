from nut import aes128
from nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from Fs.File import File
from hashlib import sha256
import  Fs.Type
import os
import re
import pathlib
from nut import Keys
from nut import Print

MEDIA_SIZE = 0x200



class Header(File):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		self.offset = 0
		self.size = 0
		self.magic = None
		self.version = None
		self.enctryCount = 0
		self.reserved = None
		super(Header, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)

	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Header, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		self.offset = self.readInt64()
		self.size = self.readInt64()
		self.magic = self.read(0x4)
		self.version = self.readInt32()
		self.enctryCount = self.readInt32()
		self.reserved = self.readInt32()

	def printInfo(self, maxDepth = 3, indent = 0):
		if not self.size:
			return

		tabs = '\t' * indent
		Print.info('\n%sBKTR' % (tabs))
		Print.info('%soffset = %d' % (tabs, self.offset))
		Print.info('%ssize = %d' % (tabs, self.size))
		Print.info('%sentry count = %d' % (tabs, self.enctryCount))
		