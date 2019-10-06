from Fs.File import File
from nut import Print
from binascii import hexlify as hx, unhexlify as uhx

class BaseFs(File):
	def __init__(self, buffer, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):		
		self.buffer = buffer
		self.sectionStart = 0
		self.fsType = None
		self.cryptoType = None
		self.size = 0
		self.cryptoCounter = None
		self.magic = None
		
		#if buffer:
		#	Hex.dump(buffer)
			
		self.files = []
		
		if buffer:
			self.buffer = buffer
			try:
				self.fsType = Fs.Type.Fs(buffer[0x3])
			except:
				self.fsType = buffer[0x3]

			try:
				self.cryptoType = Fs.Type.Crypto(buffer[0x4])
			except:
				self.cryptoType = buffer[0x4]
			
			self.cryptoCounter = bytearray((b"\x00"*8) + buffer[0x140:0x148])
			self.cryptoCounter = self.cryptoCounter[::-1]
			
			cryptoType = self.cryptoType
			cryptoCounter = self.cryptoCounter
		#else:
		#	Print.info('no sfs buffer')
			
		super(BaseFs, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)
		
	def __getitem__(self, key):
		if isinstance(key, str):
			for f in self.files:
				if (hasattr(f, 'name') and f.name == key) or (hasattr(f, '_path') and f._path == key):
					return f
		elif isinstance(key, int):
			return self.files[key]
				
		raise IOError('FS File Not Found')

	def realOffset(self):
		return self.offset - self.sectionStart
		
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info(tabs + 'magic = ' + str(self.magic))
		Print.info(tabs + 'fsType = ' + str(self.fsType))
		Print.info(tabs + 'cryptoType = ' + str(self.cryptoType))
		Print.info(tabs + 'size = ' + str(self.size))
		Print.info(tabs + 'offset = %s - (%s)' % (str(self.offset), str(self.sectionStart)))
		if self.cryptoCounter:
			Print.info(tabs + 'cryptoCounter = ' + str(hx(self.cryptoCounter)))
			
		if self.cryptoKey:
			Print.info(tabs + 'cryptoKey = ' + str(hx(self.cryptoKey)))
		
		Print.info('\n%s\t%s\n' % (tabs, '*' * 64))
		Print.info('\n%s\tFiles:\n' % (tabs))
		
		if(indent+1 < maxDepth):
			for f in self:
				f.printInfo(maxDepth, indent+1)
				Print.info('\n%s\t%s\n' % (tabs, '*' * 64))