import sys
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
from nsz.nut import Print

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
		self.addpos = self.headerSize
		self.written = False

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def write(self, value, size = None):
		super(Pfs0Stream, self).write(value, len(value))
		Print.progress('BufferCompression', {"processed": self.tell()})
		sys.stdout.flush()
		self.written = True
		pos = self.tell()
		if pos > self.actualSize:
			self.actualSize = pos

	def add(self, name, size, pleaseNoPrint = None):
		if self.written:
			self.addpos = self.tell()
			self.written = False
		Print.info(f'[ADDING]	 {name} {hex(size)} bytes to PFS0 at {hex(self.addpos)}', pleaseNoPrint)
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

	def close(self):
		if self.isOpen():
			self.seek(0)
			self.write(self.getHeader())
			super(Pfs0Stream, self).close()

	#0xff => 0x1, 0x100 => 0x20, 0x1ff => 0x1, 0x120 => 0x20
	def allign0x20(self, n):
		return 0x20-n%0x20

	def getStringTableSize(self):
		stringTableNonPadded = '\x00'.join(file['name'] for file in self.files)+'\x00'
		headerSizeNonPadded = 0x10 + len(self.files) * 0x18 + len(stringTableNonPadded)
		stringTableSizePadded = len(stringTableNonPadded) + self.allign0x20(headerSizeNonPadded)
		if self._stringTableSize == None:
			self._stringTableSize = stringTableSizePadded
		elif len(stringTableNonPadded) > self._stringTableSize:
			self._stringTableSize = len(stringTableNonPadded)
		return self._stringTableSize

	def updateHashHeader(self):
		pass

	def getFirstFileOffset(self):
		return self.files[0].offset

	def getHeader(self):
		stringTableNonPadded = '\x00'.join(file['name'] for file in self.files)+'\x00'
		stringTableSizePadded = self.getStringTableSize()
		stringTable = stringTableNonPadded + ('\x00'*(stringTableSizePadded-len(stringTableNonPadded)))
		headerSize = 0x10 + len(self.files) * 0x18 + stringTableSizePadded

		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (stringTableSizePadded).to_bytes(4, byteorder='little')
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
		self.addpos = headerSize
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
		Print.info(f'[ADDING]	 {name} {hex(size)} bytes to PFS0 at {hex(self.addpos)}', pleaseNoPrint)
		self.files.append({'name': name, 'size': size, 'offset': self.addpos})
		self.addpos += size
		return self

	def get(self, name):
		return self

	def close(self):
		pass

	#0xff => 0x1, 0x100 => 0x20, 0x1ff => 0x1, 0x120 => 0x20
	def allign0x20(self, n):
		return 0x20-n%0x20

	def getStringTableSize(self):
		stringTableNonPadded = '\x00'.join(file['name'] for file in self.files)+'\x00'
		headerSizeNonPadded = 0x10 + len(self.files) * 0x18 + len(stringTableNonPadded)
		stringTableSizePadded = len(stringTableNonPadded) + self.allign0x20(headerSizeNonPadded)
		if self._stringTableSize == None:
			self._stringTableSize = stringTableSizePadded
		elif len(stringTableNonPadded) > self._stringTableSize:
			self._stringTableSize = len(stringTableNonPadded)
		return self._stringTableSize

	def getHash(self):
		hexHash = self.binhash.hexdigest()
		return hexHash

	def updateHashHeader(self):
		stringTableNonPadded = '\x00'.join(file['name'] for file in self.files)+'\x00'
		stringTableSizePadded = self.getStringTableSize()
		stringTable = stringTableNonPadded + ('\x00'*(stringTableSizePadded-len(stringTableNonPadded)))
		headerSize = 0x10 + len(self.files) * 0x18 + stringTableSizePadded

		h = b''
		h += b'PFS0'
		h += len(self.files).to_bytes(4, byteorder='little')
		h += (stringTableSizePadded).to_bytes(4, byteorder='little')
		h += b'\x00\x00\x00\x00'

		stringOffset = 0
		for f in self.files:
			h += (f['offset'] - headerSize).to_bytes(8, byteorder='little')
			h += f['size'].to_bytes(8, byteorder='little')
			h += stringOffset.to_bytes(4, byteorder='little')
			h += b'\x00\x00\x00\x00'
			stringOffset += len(f['name']) + 1

		if len(self.files) > 0:
			if self.files[0]['offset'] - headerSize > 0:
				stringTable += '\x00' * (self.files[0]['offset'] - headerSize)
		h += stringTable.encode()

		headerHex = h.hex()
		self.binhash.update(h)



class Pfs0(BaseFs):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Pfs0, self).__init__(buffer, path, mode, cryptoType, cryptoKey, cryptoCounter)

		if buffer:
			self.size = int.from_bytes(buffer[0x48:0x50], byteorder='little', signed=False)
			self.sectionStart = int.from_bytes(buffer[0x40:0x48], byteorder='little', signed=False)
			#self.offset += sectionStart
			#self.size -= sectionStart

	#0xff => 0x1, 0x100 => 0x20, 0x1ff => 0x1, 0x120 => 0x20
	def allign0x20(self, n):
		return 0x20-n%0x20

	def getPaddedHeaderSize(self):
		stringTableNonPadded = '\x00'.join(file._path for file in self.files)+'\x00'
		headerSizeNonPadded = 0x10 + len(self.files) * 0x18 + len(stringTableNonPadded)
		return headerSizeNonPadded + self.allign0x20(headerSizeNonPadded);

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
			Print.info(f'[OPEN  ]	 {name} {hex(size)} bytes at {hex(offset)}')

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
