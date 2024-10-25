from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from nsz.Fs.File import BaseFile
from nsz.Fs.File import File
from hashlib import sha256
from nsz.Fs.Pfs0 import Pfs0
from nsz.Fs.BaseFs import BaseFs
import os
import re
from pathlib import Path
from nsz.nut import Keys
from nsz.nut import Print
from nsz import Fs

MEDIA_SIZE = 0x200

class Hfs0Stream(BaseFile):
	def __init__(self, f, mode = 'wb'):
		super(Hfs0Stream, self).__init__(f, mode)
		self.headerSize = 0x8000
		self.files = []
		self.actualSize = 0
		self.seek(self.headerSize)
		self.addpos = self.headerSize
		self.written = False

	def __enter__(self):
		return self
		
	def __exit__(self, type, value, traceback):
		self.close()

	def write(self, value, size = None):
		super(Hfs0Stream, self).write(value, len(value))
		self.written = True
		pos = self.tell()
		if pos > self.actualSize:
			self.actualSize = pos

	def add(self, name, size, pleaseNoPrint = None):
		if self.written:
			self.addpos = self.tell()
			self.written = False
		Print.info(f'[ADDING]     {name} {hex(size)} bytes to HFS0 at {hex(self.addpos)}', pleaseNoPrint)
		partition = self.partition(self.addpos, size, n = BaseFile())
		self.files.append({'name': name, 'size': size, 'offset': self.addpos, 'partition': partition})
		self.addpos += size
		return partition

	def get(self, name):
		for i in self.files:
			if i['name'] == name:
				return i['partition']
		return None

	def resize(self, name, size):
		for i in self.files:
			if i['name'] == name:
				i['size'] = size
				return True
		return False
		
	def currentFileSize(self):
		return self.f.tell() - self.files[-1]['offset']

	def close(self):
		if self.isOpen():
			self.seek(0)
			self.write(self.getHeader())
			super(Hfs0Stream, self).close()

	def updateHashHeader(self):
		pass

	def getHeader(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)+'\x00'
		
		headerSize = 0x10 + len(self.files) * 0x40 + len(stringTable)
	
		h = b''
		h += b'HFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (len(stringTable)).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'
		
		stringOffset = 0

		for f in self.files:
			sizeOfHashedRegion = 0 #0x200 if 0x200 < f['size'] else f['size']

			h += (f['offset'] - headerSize).to_bytes(8, byteorder='little')
			h += f['size'].to_bytes(8, byteorder='little')
			h += stringOffset.to_bytes(4, byteorder='little')
			h += sizeOfHashedRegion.to_bytes(4, byteorder='little')
			h += b'\x00' * 8
			h += b'\x00' * 0x20 # sha256 hash of region
			
			stringOffset += len(f['name']) + 1
			
		h += stringTable.encode()
		
		return h

class Hfs0(Pfs0):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Hfs0, self).__init__(buffer, path, mode, cryptoType, cryptoKey, cryptoCounter)

	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		r = super(BaseFs, self).open(path, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()

		self.magic = self.read(0x4);
		if self.magic != b'HFS0':
			raise IOError('Not a valid HFS0 partition %s @ %x' % (str(self.magic), self.tellAbsolute() - 4))
			

		fileCount = self.readInt32()
		stringTableSize = self.readInt32()
		self.readInt32() # junk data

		self.seek(0x10 + fileCount * 0x40)
		stringTable = self.read(stringTableSize)
		stringEndOffset = stringTableSize
		
		headerSize = 0x10 + 0x40 * fileCount + stringTableSize
		self.files = []

		for i in range(fileCount):
			i = fileCount - i - 1
			self.seek(0x10 + i * 0x40)

			offset = self.readInt64()
			size = self.readInt64()
			nameOffset = self.readInt32() # just the offset
			name = stringTable[nameOffset:stringEndOffset].decode('utf-8').rstrip(' \t\r\n\0')
			stringEndOffset = nameOffset
			Print.info(f'[OPEN  ]     {name} {hex(size)} bytes at {hex(offset)}')

			self.readInt32() # junk data

			f = Fs.factory(Path(name))

			f._path = name
			f.offset = offset
			f.size = size
			self.files.append(self.partition(offset + headerSize, f.size, f))

		self.files.reverse()

	def unpack(self, path, extractregex=r"*"):
		os.makedirs(str(path), exist_ok=True)
	
		for hfsf in self:
			filePath_str = str(path.joinpath(hfsf._path))
			if not re.match(extractregex, filePath_str):
				continue
			f = open(filePath_str, 'wb')
			hfsf.rewind()
			i = 0
	
			pageSize = 0x100000
	
			while True:
				buf = hfsf.read(pageSize)
				if len(buf) == 0:
					break
				i += len(buf)
				f.write(buf)
			f.close()
			Print.info(filePath_str)

	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sHFS0\n' % (tabs))
		super(Pfs0, self).printInfo(maxDepth, indent)
