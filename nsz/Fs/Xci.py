from binascii import hexlify as hx, unhexlify as uhx
from nsz.Fs.File import File
from nsz.Fs.File import BaseFile
from nsz.Fs.Hfs0 import Hfs0
from nsz.Fs.Hfs0 import Hfs0Stream
import os
import re
from nsz.nut import Print


MEDIA_SIZE = 0x200

class XciStream(BaseFile):
	def __init__(self, path = None, mode = 'wb', originalXciPath = None):
		os.makedirs(os.path.dirname(path), exist_ok = True)
		super(XciStream, self).__init__(path, mode)
		self.path = path
		self.f = open(path, 'wb+')
		self.start = 0

		self.files = []
		
		self.signature = b'\x00' * 0x100
		self.magic = b'\x00' * 4
		self.secureOffset = 0
		self.backupOffset = 0
		self.titleKekIndex = 0
		self.gamecardSize = 0
		self.gamecardHeaderVersion = 0
		self.gamecardFlags = 0
		self.packageId = 0
		self.validDataEndOffset = 0
		self.gamecardInfo = b'\x00' * 0x10
		
		self.hfs0Offset = 0
		self.hfs0HeaderSize = 0
		self.hfs0HeaderHash = b'\x00' * 0x20
		self.hfs0InitialDataHash = b'\x00' * 0x20
		self.secureMode = 0
		
		self.titleKeyFlag = 0
		self.keyFlag = 0
		self.normalAreaEndOffset = 0
		
		#self.gamecardInfo = GamecardInfo(self.partition(self.tell(), 0x70))
		#self.gamecardCert = GamecardCertificate(self.partition(0x7000, 0x200))

		with open(originalXciPath, 'rb') as xf:
			self.headerBuffer = xf.read(0x200) # gross hack just to get this working

		self.f.seek(0xF000)
		self.hfs0 = Hfs0Stream(self.partition(0xF000, n = BaseFile()))

	def __enter__(self):
		return self
		
	def __exit__(self, type, value, traceback):
		self.close()

	def add(self, name, size, pleaseNoPrint = None):
		Print.info(f'[ADDING]     {name} {hex(size)} bytes to XCI at {hex(self.f.tell())}', pleaseNoPrint)
		partition = self.partition(self.f.tell(), size, n = BaseFile())
		self.files.append({'name': name, 'size': size, 'offset': self.f.tell(), 'partition': partition})
		self.addpos += size
		return partition
		
	def currentFileSize(self):
		return self.f.tell() - self.files[-1]['offset']

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
			if self.hfs0:
				hfs0Size = self.hfs0.actualSize
				self.hfs0.close()
				self.hfs0 = None
			else:
				hfs0Size = 0

			self.seek(0)
			self.writeHeader()

			super(XciStream, self).close()

	def write(self, value, size = None):
		if size != None:
			value = value + '\0x00' * (size - len(value))
		return self.f.write(value)

	def writeInt8(self, value, byteorder='little', signed = False):
		return self.write(value.to_bytes(1, byteorder))
		
	def writeInt16(self, value, byteorder='little', signed = False):
		return self.write(value.to_bytes(2, byteorder))
		
	def writeInt32(self, value, byteorder='little', signed = False):
		return self.write(value.to_bytes(4, byteorder))

	def writeInt64(self, value, byteorder='little', signed = False):
		return self.write(value.to_bytes(8, byteorder))
		
	def writeHeader(self):
		self.write(self.headerBuffer) # gross hack to get this working
		return
		self.write(self.signature)
		self.write(self.magic)
		self.writeInt32(self.secureOffset)
		self.writeInt32(self.backupOffset)
		self.writeInt8(self.titleKekIndex)
		self.writeInt8(self.gamecardSize)
		self.writeInt8(self.gamecardHeaderVersion)
		self.writeInt8(self.gamecardFlags)
		self.writeInt64(self.packageId)
		self.writeInt64(self.validDataEndOffset)
		self.write(self.gamecardInfo)
		
		self.writeInt64(self.hfs0Offset)
		self.writeInt64(self.hfs0HeaderSize)
		self.write(self.hfs0HeaderHash)
		self.write(self.hfs0InitialDataHash)
		self.writeInt32(self.secureMode)
		
		self.writeInt32(self.titleKeyFlag)
		self.writeInt32(self.keyFlag)
		self.writeInt32(self.normalAreaEndOffset)
		
		#self.gamecardInfo = GamecardInfo(self.partition(self.tell(), 0x70))
		#self.gamecardCert = GamecardCertificate(self.partition(0x7000, 0x200))
		

class GamecardInfo(File):
	def __init__(self, file = None):
		super(GamecardInfo, self).__init__()
		
		self.firmwareVersion = 0
		self.accessControlFlags = 0
		self.readWaitTime = 0
		self.readWaitTime2 = 0
		self.writeWaitTime = 0
		self.writeWaitTime2 = 0
		self.firmwareMode = 0
		self.cupVersion = 0
		self.empty1 = 0
		self.updatePartitionHash = 0
		self.cupId = 0
		self.empty2 = b'\x00' * 0x38
		
		if file:
			self.open(file)
	
	def open(self, file, mode='rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(GamecardInfo, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		self.firmwareVersion = self.readInt64()
		self.accessControlFlags = self.readInt32()
		self.readWaitTime = self.readInt32()
		self.readWaitTime2 = self.readInt32()
		self.writeWaitTime = self.readInt32()
		self.writeWaitTime2 = self.readInt32()
		self.firmwareMode = self.readInt32()
		self.cupVersion = self.readInt32()
		self.empty1 = self.readInt32()
		self.updatePartitionHash = self.readInt64()
		self.cupId = self.readInt64()
		self.empty2 = self.read(0x38)
		
	def write(self):
		self.rewind()
		self.writeInt64(self.firmwareVersion)
		self.writeInt32(self.accessControlFlags)
		self.writeInt32(self.readWaitTime)
		self.writeInt32(self.readWaitTime2)
		self.writeInt32(self.writeWaitTime)
		self.writeInt32(self.writeWaitTime2)
		self.writeInt32(self.firmwareMode)
		self.writeInt32(self.cupVersion)
		self.writeInt32(self.empty1)
		self.writeInt64(self.updatePartitionHash)
		self.writeInt64(self.cupId)
		self.read(self.empty2)
		
class GamecardCertificate(File):
	def __init__(self, file = None):
		super(GamecardCertificate, self).__init__()
		self.signature = b'\x00' * 0x100
		self.magic = b'\x00' * 0x4
		self.unknown1 = b'\x00' * 0x10
		self.unknown2 = b'\x00' * 0xA
		self.data = b'\x00' * 0xD6
		
		if file:
			self.open(file)
			
	def open(self, file, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(GamecardCertificate, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()
		self.signature = self.read(0x100)
		self.magic = self.read(0x4)
		self.unknown1 = self.read(0x10)
		self.unknown2 = self.read(0xA)
		self.data = self.read(0xD6)
		
	def write(self):
		self.write(self.signature)
		self.write(self.magic)
		self.write(self.unknown1)
		self.write(self.unknown2)
		self.write(self.data)
			
class Xci(File):
	def __init__(self, file = None):
		super(Xci, self).__init__()
		
		self.headerOffset = 0x0

		self.challengeResponseAuthData = None
		self.challengeResponseAuthMac = None
		self.challengeResponseAuthNonce = None

		self.titleKey1 = None
		self.titleKey2 = None

		self.header = None
		self.signature = None
		self.magic = None
		self.secureOffset = None
		self.backupOffset = None
		self.titleKekIndex = None
		self.gamecardSize = None
		self.gamecardHeaderVersion = None
		self.gamecardFlags = None
		self.packageId = None
		self.validDataEndOffset = None
		self.gamecardInfo = None
		
		self.hfs0Offset = None
		self.hfs0HeaderSize = None
		self.hfs0HeaderHash = None
		self.hfs0InitialDataHash = None
		self.secureMode = None
		
		self.titleKeyFlag = None
		self.keyFlag = None
		self.normalAreaEndOffset = None
		
		self.gamecardInfo = None
		self.gamecardCert = None
		self.hfs0 = None
		
		if file:
			self.open(file)
		
	def isFullXci(self):
		self.seek(0x100)
		magic = self.read(0x4)
		self.seek(0x0)
		return magic != b'HEAD'

	def readKeyArea(self):
		self.packageId = self.readInt64()
		self.seek(0x10)
		self.challengeResponseAuthData = self.read(0x10)
		self.challengeResponseAuthMac = self.read(0x10)
		self.challengeResponseAuthNonce = self.read(0x10)
		self.seek(0x200)
		self.titleKey1 = self.read(0x8)
		self.titleKey2 = self.read(0x8)

	def readHeader(self):
		self.signature = self.read(0x100)
		self.magic = self.read(0x4)
		self.secureOffset = self.readInt32()
		self.backupOffset = self.readInt32()
		self.titleKekIndex = self.readInt8()
		self.gamecardSize = self.readInt8()
		self.gamecardHeaderVersion = self.readInt8()
		self.gamecardFlags = self.readInt8()
		self.packageId = self.readInt64()
		self.validDataEndOffset = self.readInt64()
		self.gamecardInfo = self.read(0x10)
		
		self.hfs0Offset = self.readInt64()
		self.hfs0HeaderSize = self.readInt64()
		self.hfs0HeaderHash = self.read(0x20)
		self.hfs0InitialDataHash = self.read(0x20)
		self.secureMode = self.readInt32()
		
		self.titleKeyFlag = self.readInt32()
		self.keyFlag = self.readInt32()
		self.normalAreaEndOffset = self.readInt32()
		
		self.gamecardInfo = GamecardInfo(self.partition(self.tell(), 0x70))
		self.gamecardCert = GamecardCertificate(self.partition(0x7000, 0x200))
		

	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		r = super(Xci, self).open(path, mode, cryptoType, cryptoKey, cryptoCounter)
		if self.isFullXci():
			self.readKeyArea()
			self.headerOffset = 0x1000
		self.seek(self.headerOffset)
		self.readHeader()
		self.seek(self.hfs0Offset + self.headerOffset)
		self.hfs0 = Hfs0(None, cryptoKey = None)
		self.partition(self.hfs0Offset + self.headerOffset, None, self.hfs0, cryptoKey = None)

	def unpack(self, path, extractregex="*"):
		os.makedirs(str(path), exist_ok=True)

		for nspF in self.hfs0:
			filePath_str = str(path.joinpath(nspF._path))
			if not re.match(extractregex, filePath_str):
				continue
			f = open(filePath_str, 'wb')
			nspF.rewind()
			i = 0

			pageSize = 0x10000

			while True:
				buf = nspF.read(pageSize)
				if len(buf) == 0:
					break
				i += len(buf)
				f.write(buf)
			f.close()
			Print.info(filePath_str)
		
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sXCI Archive\n' % (tabs))
		super(Xci, self).printInfo(maxDepth, indent)
		
		Print.info(tabs + 'magic = ' + str(self.magic))
		Print.info(tabs + 'titleKekIndex = ' + str(self.titleKekIndex))
		
		Print.info(tabs + 'gamecardCert = ' + str(hx(self.gamecardCert.magic + self.gamecardCert.unknown1 + self.gamecardCert.unknown2 + self.gamecardCert.data)))

		self.hfs0.printInfo(maxDepth, indent)

