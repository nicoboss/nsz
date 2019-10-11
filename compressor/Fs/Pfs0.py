from nut import aes128
from nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from Fs.File import File
from hashlib import sha256
import Fs.Type
import os
import re
import pathlib
from nut import Keys
from nut import Print
from Fs.BaseFs import BaseFs
from nut import Titles

MEDIA_SIZE = 0x200

class Pfs0Stream():
	def __init__(self, path):
		os.makedirs(os.path.dirname(path), exist_ok = True)
		self.path = path
		self.f = open(path, 'wb')
		self.offset = 0x8000
		self.files = []

		self.f.seek(self.offset)

	def add(self, name, size):
		Print.info('Adding file %s %d bytes to NSP' % (name, int(size)))
		self.files.append({'name': name, 'size': size, 'offset': self.f.tell()})
		t = {'name': name, 'size': size, 'offset': self.f.tell()}
		return self.f

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
		self.f.seek(0)
		self.f.write(self.getHeader())
		self.f.close()

	def getHeader(self):
		stringTable = '\x00'.join(file['name'] for file in self.files)
		
		headerSize = 0x10 + len(self.files) * 0x18 + len(stringTable)
		remainder = 0x10 - headerSize % 0x10
		headerSize += remainder
	
		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (len(stringTable)+remainder).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'
		
		stringOffset = 0

		for f in self.files:
			h += (f['offset'] - headerSize).to_bytes(8, byteorder='little')
			h += f['size'].to_bytes(8, byteorder='little')
			h += stringOffset.to_bytes(4, byteorder='little')
			h += b'\x00\x00\x00\x00'
			
			stringOffset += len(f['name']) + 1
			
		h += stringTable.encode()
		h += remainder * b'\x00'
		
		return h
		
class Pfs0(BaseFs):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Pfs0, self).__init__(buffer, path, mode, cryptoType, cryptoKey, cryptoCounter)
		
		if buffer:
			self.size = int.from_bytes(buffer[0x48:0x50], byteorder='little', signed=False)
			self.sectionStart = int.from_bytes(buffer[0x40:0x48], byteorder='little', signed=False)
			#self.offset += sectionStart
			#self.size -= sectionStart
		
	def getHeader():
		stringTable = '\x00'.join(file.name for file in self.files)
		
		headerSize = 0x10 + len(self.files) * 0x18 + len(stringTable)
		remainder = 0x10 - headerSize % 0x10
		headerSize += remainder
	
		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (len(stringTable)+remainder).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'
		
		stringOffset = 0
		
		for f in range(len(self.files)):
			header += f.offset.to_bytes(8, byteorder='little')
			header += f.size.to_bytes(8, byteorder='little')
			header += stringOffset.to_bytes(4, byteorder='little')
			header += b'\x00\x00\x00\x00'
			
			stringOffset += len(f.name) + 1
			
		h += stringTable.encode()
		h += remainder * b'\x00'
		
		return h
		
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
		stringTableSize = self.readInt32()
		self.readInt32() # junk data

		self.seek(0x10 + fileCount * 0x18)
		stringTable = self.read(stringTableSize)
		stringEndOffset = stringTableSize
		
		headerSize = 0x10 + 0x18 * fileCount + stringTableSize
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

			f = Fs.factory(name)

			f._path = name
			f.offset = offset
			f.size = size
			
			self.files.append(self.partition(offset + headerSize, f.size, f, autoOpen = False))

		ticket = None


		try:
			ticket = self.ticket()
			ticket.open(None, None)
			#key = format(ticket.getTitleKeyBlock(), 'X').zfill(32)
			
			if ticket.titleKey() != ('0' * 32):
				Titles.get(ticket.titleId()).key = ticket.titleKey()
		except:
			Print.info('no ticket found')

		for i in range(fileCount):
			if self.files[i] != ticket:
				self.files[i].open(None, None)

		self.files.reverse()
				
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sPFS0\n' % (tabs))
		super(Pfs0, self).printInfo(maxDepth, indent)
