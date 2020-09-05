from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from hashlib import sha256
import os
import re
import pathlib
from nsz.nut import Keys
from nsz.nut import Print
from nsz import Fs
from nsz import nut
from nsz.Fs.File import File
from nsz.Fs.Rom import Rom
from nsz.Fs.Pfs0 import Pfs0
from nsz.Fs.BaseFs import BaseFs
from nsz.nut import Titles

MEDIA_SIZE = 0x200


class SectionTableEntry:
	def __init__(self, d):
		self.mediaOffset = int.from_bytes(d[0x0:0x4], byteorder='little', signed=False)
		self.mediaEndOffset = int.from_bytes(d[0x4:0x8], byteorder='little', signed=False)
		
		self.offset = self.mediaOffset * MEDIA_SIZE
		self.endOffset = self.mediaEndOffset * MEDIA_SIZE
		
		self.unknown1 = int.from_bytes(d[0x8:0xc], byteorder='little', signed=False)
		self.unknown2 = int.from_bytes(d[0xc:0x10], byteorder='little', signed=False)
		self.sha1 = None
		
	
def GetSectionFilesystem(buffer, cryptoKey):
	fsType = buffer[0x3]
	if fsType == Fs.Type.Fs.PFS0:
		return Pfs0(buffer, cryptoKey = cryptoKey)
		
	if fsType == Fs.Type.Fs.ROMFS:
		return Rom(buffer, cryptoKey = cryptoKey)
		
	return BaseFs(buffer, cryptoKey = cryptoKey)
	
class NcaHeader(File):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		self.signature1 = None
		self.signature2 = None
		self.magic = None
		self.isGameCard = None
		self.contentType = None
		self.cryptoType = None
		self.keyIndex = None
		self.size = None
		self.titleId = None
		self.contentIndex = None
		self.sdkVersion = None
		self.cryptoType2 = None
		self.rightsId = None
		self.titleKeyDec = None
		self.masterKey = None
		self.sectionTables = []
		self.keys = []
		
		super(NcaHeader, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)
		
	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(NcaHeader, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		self.signature1 = self.read(0x100)
		self.signature2 = self.read(0x100)
		self.magic = self.read(0x4)
		self.isGameCard = self.readInt8()
		self.contentType = self.readInt8()

		try:
			self.contentType = Fs.Type.Content(self.contentType)
		except:
			pass

		self.cryptoType = self.readInt8()
		self.keyIndex = self.readInt8()
		self.size = self.readInt64()
		self.titleId = hx(self.read(8)[::-1]).decode('utf-8').upper()
		self.contentIndex = self.readInt32()
		self.sdkVersion = self.readInt32()
		self.cryptoType2 = self.readInt8()
		
		self.read(0xF) # padding
		
		self.rightsId = hx(self.read(0x10))
		
		if self.magic not in [b'NCA3', b'NCA2']:
			raise Exception('Failed to decrypt NCA header: ' + str(self.magic))
		
		self.sectionHashes = []
		
		for i in range(4):
			self.sectionTables.append(SectionTableEntry(self.read(0x10)))
			
		for i in range(4):
			self.sectionHashes.append(self.sectionTables[i])

		self.masterKey = (self.cryptoType if self.cryptoType > self.cryptoType2 else self.cryptoType2)-1

		if self.masterKey < 0:
			self.masterKey = 0
		
		
		self.encKeyBlock = self.getKeyBlock()
		#for i in range(4):
		#	offset = i * 0x10
		#	key = encKeyBlock[offset:offset+0x10]
		#	Print.info('enc %d: %s' % (i, hx(key)))


		#crypto = aes128.AESECB(Keys.keyAreaKey(self.masterKey, 0))
		self.keyBlock = Keys.unwrapAesWrappedTitlekey(self.encKeyBlock, self.masterKey)
		self.keys = []
		for i in range(4):
			offset = i * 0x10
			key = self.keyBlock[offset:offset+0x10]
			#Print.info('dec %d: %s' % (i, hx(key)))
			self.keys.append(key)

		if self.hasTitleRights():
			titleRightsTitleId = self.rightsId.decode()[0:16].upper()

			if titleRightsTitleId in Titles.keys() and Titles.get(titleRightsTitleId).key:
				self.titleKeyDec = Keys.decryptTitleKey(uhx(Titles.get(titleRightsTitleId).key), self.masterKey)
			else:
				Print.info('could not find title key %s!' % titleRightsTitleId)
		else:
			self.titleKeyDec = self.key()

		return True

	def realTitleId(self):
		if not self.hasTitleRights():
			return self.titleId

		return self.getRightsIdStr()[0:16]

	def key(self):
		return self.keys[2]

	def hasTitleRights(self):
		return self.rightsId != (b'0' * 32)

	def getKeyBlock(self):
		self.seek(0x300)
		return self.read(0x40)

	def setKeyBlock(self, value):
		if len(value) != 0x40:
			raise IOError('invalid keyblock size')

		self.seek(0x300)
		return self.write(value)

	def getCryptoType(self):
		self.seek(0x206)
		return self.readInt8()

	def setCryptoType(self, value):
		self.seek(0x206)
		self.writeInt8(value)

	def getCryptoType2(self):
		self.seek(0x220)
		return self.readInt8()

	def setCryptoType2(self, value):
		self.seek(0x220)
		self.writeInt8(value)

	def getRightsId(self):
		self.seek(0x230)
		return self.readInt128('big')

	def getRightsIdStr(self):
		self.seek(0x230)
		return hx(self.read(16)).decode()

	def setRightsId(self, value):
		self.seek(0x230)
		self.writeInt128(value, 'big')

	def getIsGameCard(self):
		self.seek(0x204)
		return self.readInt8()

	def setIsGameCard(self, value):
		self.seek(0x204)
		self.writeInt8(value)


class Nca(File):
	def __init__(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		self.header = None
		self.sectionFilesystems = []
		self.sections = []
		super(Nca, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)
			
	def __iter__(self):
		return self.sectionFilesystems.__iter__()
		
	def __getitem__(self, key):
		return self.sectionFilesystems[key]

	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Nca, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)

		self.header = NcaHeader()
		self.partition(0x0, 0xC00, self.header, Fs.Type.Crypto.XTS, uhx(Keys.get('header_key')))
		#Print.info('partition complete, seeking')
		self.header.seek(0x400)
		#Print.info('reading')
		#Hex.dump(self.header.read(0x200))
		#sys.exit()

		for i in range(4):
			hdr = self.header.read(0x200)
			section = BaseFs(hdr, cryptoKey = self.header.titleKeyDec)
			fs = GetSectionFilesystem(hdr, cryptoKey = -1)
			#Print.info('fs type = ' + hex(fs.fsType))
			#Print.info('fs crypto = ' + hex(fs.cryptoType))
			#Print.info('st end offset = ' + str(self.header.sectionTables[i].endOffset - self.header.sectionTables[i].offset))
			#Print.info('fs offset = ' + hex(self.header.sectionTables[i].offset))
			#Print.info('fs section start = ' + hex(fs.sectionStart))
			#Print.info('titleKey = ' + hex(self.header.titleKeyDec))

			self.partition(self.header.sectionTables[i].offset, self.header.sectionTables[i].endOffset - self.header.sectionTables[i].offset, section, cryptoKey = self.header.titleKeyDec)

			try:
				section.partition(fs.sectionStart, section.size - fs.sectionStart, fs)
			except BaseException as e:
				pass
				#Print.info(e)
				#raise

			if fs.fsType:
				self.sectionFilesystems.append(fs)
				self.sections.append(section)
				
			fs.open(None, 'rb')
		
		
		self.titleKeyDec = None

	def masterKey(self):
		return max(self.header.cryptoType, self.header.cryptoType2)

	def buildId(self):
		if self.header.contentType != Fs.Type.Content.PROGRAM:
			return None

		try:
			f = self[0]['main']
			f.seek(0x40)
			return hx(f.read(0x20)).decode('utf8').upper()
		except IOError as e:
			pass
		except:
			raise
			return None
		
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sNCA Archive\n' % (tabs))
		super(Nca, self).printInfo(maxDepth, indent)
		
		Print.info(tabs + 'magic = ' + str(self.header.magic))
		Print.info(tabs + 'titleId = ' + str(self.header.titleId))
		Print.info(tabs + 'rightsId = ' + str(self.header.rightsId))
		Print.info(tabs + 'isGameCard = ' + hex(self.header.isGameCard))
		Print.info(tabs + 'contentType = ' + str(self.header.contentType))
		Print.info(tabs + 'cryptoType = ' + str(self.cryptoType))
		Print.info(tabs + 'Size: ' + str(self.header.size))
		Print.info(tabs + 'crypto master key: ' + str(self.header.cryptoType))
		Print.info(tabs + 'crypto master key2: ' + str(self.header.cryptoType2))
		Print.info(tabs + 'key Index: ' + str(self.header.keyIndex))
		#Print.info(tabs + 'key Block: ' + str(self.header.getKeyBlock()))
		for key in self.header.keys:
			if key:
				Print.info(tabs + 'key Block: ' + str(hx(key)))
		
		if(indent+1 < maxDepth):
			Print.info('\n%sPartitions:' % (tabs))
		
			for s in self:
				s.printInfo(maxDepth, indent+1)

		if self.header.contentType == Fs.Type.Content.PROGRAM:
			Print.info(tabs + 'build Id: ' + str(self.buildId()))
