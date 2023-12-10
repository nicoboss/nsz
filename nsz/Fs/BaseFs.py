# from nsz import Fs
from nsz.Fs.File import File
from nsz.Fs import Type
from nsz.nut import Print
from nsz.Fs.File import MemoryFile
from nsz.Fs.Cnmt import Cnmt
from nsz.Fs import Bktr
from binascii import hexlify as hx, unhexlify as uhx

class EncryptedSection:
	def __init__(self, offset, size, cryotoType, cryptoKey, cryptoCounter):
		self.offset = offset
		self.size = size
		self.cryptoType = cryotoType
		self.cryptoKey = cryptoKey
		self.cryptoCounter = cryptoCounter

class BaseFs(File):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):		
		self.buffer = buffer
		self.sectionStart = 0
		self.fsType = None
		self.cryptoType = None
		self.size = 0
		self.cryptoCounter = None
		self.magic = None
		self._headerSize = None
		self.bktrRelocation = None
		self.bktrSubsection = None
			
		self.files = []
		
		if buffer:
			self.buffer = buffer
			try:
				self.fsType = Type.Fs(buffer[0x3])
			except:
				self.fsType = buffer[0x3]

			try:
				self.cryptoType = Type.Crypto(buffer[0x4])
			except:
				self.cryptoType = buffer[0x4]
			
			self.cryptoCounter = bytearray((b"\x00"*8) + buffer[0x140:0x148])
			self.cryptoCounter = self.cryptoCounter[::-1]
			
			cryptoType = self.cryptoType
			cryptoCounter = self.cryptoCounter
			
			self.bktr1Buffer = buffer[0x100:0x120]
			self.bktr2Buffer = buffer[0x120:0x140]
		else:
			self.bktr1Buffer = None
			self.bktr2Buffer = None
			
		super(BaseFs, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)
		
	def __getitem__(self, key):
		if isinstance(key, str):
			for f in self.files:
				if (hasattr(f, 'name') and f.name == key) or (hasattr(f, '_path') and f._path == key):
					return f
		elif isinstance(key, int):
			return self.files[key]
				
		raise IOError('FS File Not Found')
		
	def getEncryptionSections(self):
		sections = []
		
		if self.hasBktr():
			sectionOffset = self.realOffset()

			for entry in self.bktrSubsection.getAllEntries():
				ctr = self.setBktrCounter(entry.ctr, 0)
				sections.append(EncryptedSection(self.realOffset() + entry.virtualOffset, entry.size, self.cryptoType, self.cryptoKey, ctr))
			
			if len(sections) == 0:
				sections.append(EncryptedSection(sectionOffset, self.size, self.cryptoType, self.cryptoKey, self.cryptoCounter))
			else:
				offset = sections[-1].offset + sections[-1].size
				sections.append(EncryptedSection(offset, (sectionOffset + self.size) - offset, self.cryptoType, self.cryptoKey, self.cryptoCounter))
				
		else:
			sections.append(EncryptedSection(self.realOffset(), self.size, self.cryptoType, self.cryptoKey, self.cryptoCounter))
		return sections

	def realOffset(self):
		return self.offset - self.sectionStart
		
	def hasBktr(self):
		return (False if self.bktrSubsection is None else True) and self.bktrSubsection.isValid()
		
		
	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		r = super(BaseFs, self).open(path, mode, cryptoType, cryptoKey, cryptoCounter)

		if self.bktr1Buffer:
			try:
				self.bktrRelocation = Bktr.Bktr1(MemoryFile(self.bktr1Buffer), 'rb', nca = self)
			except BaseException as e:
				Print.info('bktr reloc exception: ' + str(e))
			
		if self.bktr2Buffer:
			try:
				self.bktrSubsection = Bktr.Bktr2(MemoryFile(self.bktr2Buffer), 'rb', nca = self)
			except BaseException as e:
				Print.info('bktr subsection exception: ' + str(e))
		
	def bktrRead(self, size = None, direct = False):
		self.cryptoOffset = 0
		self.ctr_val = 0
		'''
		if self.bktrRelocation:
			entry = self.bktrRelocation.getRelocationEntry(self.tell())
		
			if entry:
				self.ctr_val = entry.ctr
				#self.cryptoOffset = entry.virtualOffset + entry.physicalOffset
		'''
		if self.bktrSubsection is not None:
			entries = self.bktrSubsection.getEntries(self.tell(), size)
			#print('offset = %x' % self.tell())
			for entry in entries:
				#print('offset = %x' % self.tell())
				entry.printInfo()
				#sys.exit(0)
		#else:
		#	print('unknown offset = %x' % self.tell())
				
		return super(BaseFs, self).read(size, direct)
		
	def read(self, size = None, direct = False):
		'''
		if self.cryptoType == Type.Crypto.BKTR or self.bktrSubsection is not None:
			return self.bktrRead(size, True)
		else:
			return super(BaseFs, self).read(size, direct)
		'''
		return super(BaseFs, self).read(size, direct)
		
	def getCnmt(self):
		for f in self:
			if isinstance(f, Cnmt):
				return f
		raise("No Cnmt found!")
	
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info(f'{tabs}magic = {self.magic}')
		Print.info(f'{tabs}fsType = {self.fsType}')
		Print.info(f'{tabs}cryptoType = {self.cryptoType}')
		Print.info(f'{tabs}size = {hex(self.size)}')
		Print.info(f'{tabs}headerSize = {self._headerSize}')
		Print.info(f'{tabs}offset = {hex(self.offset)} - ({hex(self.sectionStart)})')
		if self.cryptoCounter:
			Print.info(f'{tabs}cryptoCounter = {hx(self.cryptoCounter)}')
			
		if self.cryptoKey:
			Print.info(f'{tabs}cryptoKey = {hx(self.cryptoKey)}')
		
		Print.info('\n%s\t%s\n' % (tabs, '*' * 64))
		Print.info('\n%s\tFiles:\n' % (tabs))
		
		if(indent+1 < maxDepth):
			for f in self:
				f.printInfo(maxDepth, indent+1)
				Print.info('\n%s\t%s\n' % (tabs, '*' * 64))
				
		if self.bktrRelocation:
			self.bktrRelocation.printInfo(maxDepth, indent+1)

		if self.bktrSubsection:
			self.bktrSubsection.printInfo(maxDepth, indent+1)