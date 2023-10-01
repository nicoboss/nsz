from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from nsz.Fs.File import File
from nsz.Fs.File import BaseFile
from hashlib import sha256
from nsz import Fs
import os
import re
from pathlib import Path
from nsz.nut import Keys
from nsz.nut import Print
from nsz.Fs.BaseFs import BaseFs
from nsz.nut import Titles

MEDIA_SIZE = 0x200

class Pfs0Stream(BaseFile):
	def __init__(self, headerSize, stringTableSize, path, mode = 'wb'):
		os.makedirs(os.path.dirname(path), exist_ok = True)
		super(Pfs0Stream, self).__init__(path, mode)
		self.headerSize = headerSize
		self._stringTableSize = stringTableSize
		self.files = []
		
		self.actualSize = 0

		self.f.seek(self.headerSize)

	def __enter__(self):
		return self
		
	def __exit__(self, type, value, traceback):
		self.close()
		
	def write(self, value, size = None):
		super(Pfs0Stream, self).write(value, len(value))
		if self.tell() > self.actualSize:
			self.actualSize = self.tell()

	def add(self, name, size, pleaseNoPrint = None):
		Print.info('[ADDING]     {0} {1} bytes to NSP'.format(name, size), pleaseNoPrint)
		self.files.append({'name': name, 'size': size, 'offset': self.f.tell()})
		return self.partition(self.f.tell(), size, n = BaseFile())

	def get(self, name):
		for i in self.files:
			if i['name'] == name:
				return i
		return None

	def resize(self, name, size):
		for i in self.files:
			if i['name'] == name:
				i['size'] = size
				return True
		return False

	def close(self):
		if self.isOpen():
			self.seek(0)
			self.write(self.getHeader())
			super(Pfs0Stream, self).close()
			
	def getHeaderSize(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		headerSize = 0x10 + len(self.files) * 0x18 + self.stringTableSize
		return headerSize
	
	def getStringTableSize(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		stringTableLen = len(stringTable)
		if self._stringTableSize == None:
			self._stringTableSize = stringTableLen
		if stringTableLen > self._stringTableSize:
			self._stringTableSize = stringTableLen
		return self._stringTableSize

	def getFirstFileOffset(self):
		return self.files[0].offset

	def getHeader(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		headerSize = 0x10 + len(self.files) * 0x18 + self.getStringTableSize()
	
		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (self.getStringTableSize()).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'
		
		stringOffset = 0

		for f in self.files:
			h += (f['offset'] - headerSize).to_bytes(8, byteorder='little')
			h += f['size'].to_bytes(8, byteorder='little')
			h += stringOffset.to_bytes(4, byteorder='little')
			h += b'\x00\x00\x00\x00'
			
			stringOffset += len(f['name']) + 1
			
		h += stringTable.encode()
		
		return h


class Pfs0VerifyStream():
	def __init__(self, headerSize, stringTableSize, mode = 'wb'):
		self.files = []
		self.binhash = sha256()
		self.pos = headerSize
		self._stringTableSize = stringTableSize

	def __enter__(self):
		return self
		
	def __exit__(self, type, value, traceback):
		pass
		
	def write(self, value, size = None):
		self.binhash.update(value)
		self.pos += len(value)

	def tell(self):
		return self.pos

	def add(self, name, size, pleaseNoPrint = None):
		Print.info('[ADDING]     {0} {1} bytes to NSP'.format(name, size), pleaseNoPrint)
		self.files.append({'name': name, 'size': size, 'offset': self.pos})
		return self

	def resize(self, name, size):
		for i in self.files:
			if i['name'] == name:
				i['size'] = size
				return True
		return False

	def close(self):
		pass
	
	def getStringTableSize(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		stringTableLen = len(stringTable)
		if self._stringTableSize == None:
			self._stringTableSize = stringTableLen
		if stringTableLen > self._stringTableSize:
			self._stringTableSize = stringTableLen
		return self._stringTableSize
	
	def getHash(self):
		hexHash = self.binhash.hexdigest()
		return hexHash

	def getHeaderHash(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		headerSize = 0x10 + len(self.files) * 0x18 + self.getStringTableSize()
	
		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (self.getStringTableSize()).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'
		
		stringOffset = 0
		
		for f in self.files:
			h += (f['offset'] - headerSize).to_bytes(8, byteorder='little')
			h += f['size'].to_bytes(8, byteorder='little')
			h += stringOffset.to_bytes(4, byteorder='little')
			h += b'\x00\x00\x00\x00'
			
			stringOffset += len(f['name']) + 1
			
		h += stringTable.encode()
		
		headerBinhash = sha256()
		headerBinhash.update(h)
		headerHexHash = headerBinhash.hexdigest()
		return headerHexHash


class Pfs0(BaseFs):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Pfs0, self).__init__(buffer, path, mode, cryptoType, cryptoKey, cryptoCounter)
		
		if buffer:
			self.size = int.from_bytes(buffer[0x48:0x50], byteorder='little', signed=False)
			self.sectionStart = int.from_bytes(buffer[0x40:0x48], byteorder='little', signed=False)
			#self.offset += sectionStart
			#self.size -= sectionStart

	def getHeaderSize(self):
		return self._headerSize;
	
	def getStringTableSize(self):
		return self._stringTableSize;

	def getFirstFileOffset(self):
		return self.files[0].offset

	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		r = super(Pfs0, self).open(path, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		#self.setupCrypto()
		#Print.info('cryptoType = ' + hex(self.cryptoType))
		#Print.info('titleKey = ' + (self.cryptoKey.hex()))
		#Print.info('cryptoCounter = ' + (self.cryptoCounter.hex()))

		self.magic = self.read(4)
		if self.magic != b'PFS0':
			raise IOError('Not a valid PFS0 partition ' + str(self.magic))
			

		fileCount = self.readInt32()
		self._stringTableSize = self.readInt32()
		self.readInt32() # junk data

		self.seek(0x10 + fileCount * 0x18)
		stringTable = self.read(self._stringTableSize)
		stringEndOffset = self._stringTableSize
		
		self._headerSize = 0x10 + 0x18 * fileCount + self._stringTableSize
		self.files = []

		for i in range(fileCount):
			i = fileCount - i - 1
			self.seek(0x10 + i * 0x18)

			offset = self.readInt64()
			size = self.readInt64()
			nameOffset = self.readInt32() # just the offset
			name = stringTable[nameOffset:stringEndOffset].decode('utf-8').rstrip(' \t\r\n\0')
			stringEndOffset = nameOffset

			self.readInt32() # junk data

			f = Fs.factory(Path(name))

			f._path = name
			f.offset = offset
			f.size = size
			
			self.files.append(self.partition(offset + self._headerSize, f.size, f, autoOpen = False))

		ticket = None


		try:
			ticket = self.ticket()
			ticket.open(None, None)
			#key = format(ticket.getTitleKeyBlock(), 'X').zfill(32)
			
			if ticket.titleKey() != ('0' * 32):
				Titles.get(ticket.titleId()).key = ticket.titleKey()
		except:
			pass

		for i in range(fileCount):
			if self.files[i] != ticket:
				try:
					self.files[i].open(None, None)
				except:
					pass

		self.files.reverse()
				
	
	def getCnmt(self):
		return super(Pfs0, self).getCnmt()
	
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sPFS0\n' % (tabs))
		super(Pfs0, self).printInfo(maxDepth, indent)
