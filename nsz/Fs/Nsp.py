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
from Fs.Pfs0 import Pfs0
from Fs.Ticket import Ticket
from Fs.Nca import Nca
import shutil
from tqdm import tqdm

MEDIA_SIZE = 0x200

class Nsp(Pfs0):
	def __init__(self, path = None, mode = 'rb'):
		self.path = None
		self.titleId = None
		self.hasValidTicket = None
		self.timestamp = None
		self.version = None
		self.fileSize = None
		self.fileModified = None
		self.extractedNcaMeta = False

		super(Nsp, self).__init__(None, path, mode)
		
		if path:
			self.setPath(path)
			#if files:
			#	self.pack(files)
				
		if self.titleId and self.isUnlockable():
			Print.info('unlockable title found ' + self.path)
		#	self.unlock()

	def getFileSize(self):
		if self.fileSize == None:
			self.fileSize = os.path.getsize(self.path)
		return self.fileSize

	def getFileModified(self):
		if self.fileModified == None:
			self.fileModified = os.path.getmtime(self.path)
		return self.fileModified

	def loadCsv(self, line, map = ['id', 'path', 'version', 'timestamp', 'hasValidTicket', 'extractedNcaMeta']):
		split = line.split('|')
		for i, value in enumerate(split):
			if i >= len(map):
				Print.info('invalid map index: ' + str(i) + ', ' + str(len(map)))
				continue
			
			i = str(map[i])
			methodName = 'set' + i[0].capitalize() + i[1:]
			method = getattr(self, methodName, lambda x: None)
			method(value.strip())

	def serialize(self, map = ['id', 'path', 'version', 'timestamp', 'hasValidTicket', 'extractedNcaMeta']):
		r = []
		for i in map:
				
			methodName = 'get' + i[0].capitalize() + i[1:]
			method = getattr(self, methodName, lambda: methodName)
			r.append(str(method()))
		return '|'.join(r)

	def __lt__(self, other):
		return str(self.path) < str(other.path)
				
	def __iter__(self):
		return self.files.__iter__()
		
	def title(self):
		if not self.titleId:
			raise IOError('NSP no titleId set')
			
		if self.titleId in Titles.keys():
			return Titles.get(self.titleId)
			
		t = Title.Title()
		t.setId(self.titleId)
		Titles.data()[self.titleId] = t
		return t

	def getUpdateFile(self):
		title = self.title()

		if title.isUpdate or title.isDLC or not title.updateId:
			return None

		for i, nsp in Nsps.files.items():
			if nsp.titleId == title.updateId:
				return nsp

		return None

	def unpack(self, path, extractregex="*"):
		os.makedirs(str(path), exist_ok=True)

		for nspF in self:
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

	def setHasValidTicket(self, value):
		if hasattr(self.title(), 'isUpdate') and self.title().isUpdate:
			self.hasValidTicket = True
			return

		try:
			self.hasValidTicket = (True if value and int(value) != 0 else False) or self.title().isUpdate
		except:
			pass

	#extractedNcaMeta

	def getExtractedNcaMeta(self):
		if hasattr(self, 'extractedNcaMeta') and self.extractedNcaMeta == True:
			return 1
		return 0

	def setExtractedNcaMeta(self, val):
		if val and (val != 0 or val == True):
			self.extractedNcaMeta = True
		else:
			self.extractedNcaMeta = False

	def getHasValidTicket(self):
		if self.title().isUpdate:
			return 1
		return (1 if self.hasValidTicket and self.hasValidTicket == True else 0)

	def setId(self, id):
		if re.match('[A-F0-9]{16}', id, re.I):
			self.titleId = id

	def getId(self):
			return self.titleId or ('0' * 16)

	def setTimestamp(self, timestamp):
		try:
			self.timestamp = int(str(timestamp), 10)
		except:
			pass

	def getTimestamp(self):
		return str(self.timestamp or '')

	def setVersion(self, version):
		if version and len(version) > 0:
			self.version = version

	def getVersion(self):
		return self.version or ''
			
	def setPath(self, path):			
		self.path = path
		self.version = '0'
		
		z = re.match('.*\[([a-zA-Z0-9]{16})\].*', path, re.I)
		if z:
			self.titleId = z.groups()[0].upper()
		else:
			Print.info('could not get title id from filename, name needs to contain [titleId] : ' + path)
			self.titleId = None

		z = re.match('.*\[v([0-9]+)\].*', path, re.I)
		
		if z:
			self.version = z.groups()[0]

		if path.endswith('.nsp'):
			if self.hasValidTicket is None:
				self.setHasValidTicket(True)
		elif path.endswith('.nsx'):
			if self.hasValidTicket is None:
				self.setHasValidTicket(False)
		else:
			print('unknown extension ' + str(path))
			return

	def getPath(self):
		return self.path or ''
			
	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Nsp, self).open(path or self.path, mode, cryptoType, cryptoKey, cryptoCounter)
					
	def move(self, forceNsp = False):
		if not self.path:
			Print.error('no path set')
			return False
			
		newPath = self.fileName(forceNsp = forceNsp)
		
		if not newPath:
			Print.error('could not get filename for ' + self.path)
			return False

		if os.path.abspath(newPath).lower().replace('\\', '/') == os.path.abspath(self.path).lower().replace('\\', '/'):
			return False
			
		if os.path.isfile(newPath):
			Print.info('duplicate title: ')
			Print.info(os.path.abspath(self.path))
			Print.info(os.path.abspath(self.fileName(forceNsp = forceNsp)))
			return False

		try:
			Print.info(self.path + ' -> ' + self.fileName(forceNsp = forceNsp))
			
			if not Config.dryRun:
				os.makedirs(os.path.dirname(self.fileName(forceNsp = forceNsp)), exist_ok=True)
			newPath = self.fileName(forceNsp = forceNsp)
			
			if not Config.dryRun:
				shutil.move(self.path, newPath)
				self.path = newPath
		except BaseException as e:
			Print.error('failed to rename file! %s -> %s  : %s' % (self.path, self.fileName(forceNsp = forceNsp), e))
			if not Config.dryRun:
				self.moveDupe()
					
		
		return True

	def moveDupe(self):
		if Config.dryRun:
			return True

		try:
			newPath = self.fileName()
			os.makedirs(Config.paths.duplicates, exist_ok = True)
			origDupePath = Config.paths.duplicates + os.path.basename(newPath)
			dupePath = origDupePath
			Print.info('moving duplicate ' + os.path.basename(newPath))
			c = 0
			while os.path.isfile(dupePath):
				dupePath = Config.paths.duplicates + os.path.basename(newPath) + '.' + str(c)
				c = c + 1
			shutil.move(self.path, dupePath)
			return True
		except BaseException as e:
			Print.error('failed to move to duplicates! ' + str(e))
		return False
		
	def cleanFilename(self, s):
		if s is None:
			return ''
		#s = re.sub('\s+\Demo\s*', ' ', s, re.I)
		s = re.sub('\s*\[DLC\]\s*', '', s, re.I)
		s = re.sub(r'[\/\\\:\*\?\"\<\>\|\.\s™©®()\~]+', ' ', s)
		return s.strip()

	def dict(self):
		return {"titleId": self.titleId, "hasValidTicket": self.hasValidTicket, 'extractedNcaMeta': self.getExtractedNcaMeta(), 'version': self.version, 'timestamp': self.timestamp, 'path': self.path }
		
	def fileName(self, forceNsp = False):
		bt = None
		if not self.titleId in Titles.keys():
			if not Title.getBaseId(self.titleId) in Titles.keys():
				Print.info('could not find base title for ' + str(self.titleId) + ' or ' + str(Title.getBaseId(self.titleId)))
				return None
			bt = Titles.get(Title.getBaseId(self.titleId))
			t = Title.Title()
			if bt.name is not None:
				t.loadCsv(self.titleId + '0000000000000000|0000000000000000|' + bt.name)
			else:
				t.setId(self.titleId)
		else:
			t = Titles.get(self.titleId)

			if not t:
				Print.error('could not find title id ' + str(self.titleId))
				return None
		
			try:
				if not t.baseId in Titles.keys():
					Print.info('could not find baseId for ' + self.path)
					return None
			except BaseException as e:
				print('exception: could not find title id ' + str(self.titleId) + ' ' + str(e))
				return None
			bt = Titles.get(t.baseId)
			
			
		isNsx = not self.hasValidTicket and not forceNsp
		
		if t.isDLC:
			format = Config.paths.getTitleDLC(isNsx)
		elif t.isDemo:
			if t.idExt != 0:
				format = Config.paths.getTitleDemoUpdate(isNsx)
			else:
				format = Config.paths.getTitleDemo(isNsx)
		elif t.idExt != 0:
			if bt and bt.isDemo:
				format = Config.paths.getTitleDemoUpdate(isNsx)
			else:
				format = Config.paths.getTitleUpdate(isNsx)
		else:
			format = Config.paths.getTitleBase(isNsx)
			
		format = format.replace('{id}', self.cleanFilename(t.id))
		format = format.replace('{region}', self.cleanFilename(t.getRegion() or bt.getRegion()))
		format = format.replace('{name}', self.cleanFilename(t.getName() or ''))
		format = format.replace('{version}', str(self.getVersion() or 0))
		format = format.replace('{baseId}', self.cleanFilename(bt.id))

		baseName = self.cleanFilename(bt.getName() or '')
		result = format.replace('{baseName}', baseName)
		
		while(len(os.path.basename(result).encode('utf-8')) > 240 and len(baseName) > 3):
			baseName = baseName[:-1]
			result = format.replace('{baseName}', baseName)
			
		
		return result
		
	def ticket(self):
		for f in (f for f in self if type(f) == Ticket):
			return f
		raise IOError('no ticket in NSP')
		
	def cnmt(self):
		for f in (f for f in self if f._path.endswith('.cnmt.nca')):
			return f
		raise IOError('no cnmt in NSP')

	def xml(self):
		for f in (f for f in self if f._path.endswith('.xml')):
			return f
		raise IOError('no XML in NSP')

	def hasDeltas(self):
		return b'DeltaFragment' in self.xml().read()
		
	def application(self):
		for f in (f for f in self if f._path.endswith('.nca') and not f._path.endswith('.cnmt.nca')):
			return f
		raise IOError('no application in NSP')
		
	def isUnlockable(self):
		return (not self.hasValidTicket) and self.titleId and Titles.contains(self.titleId) and Titles.get(self.titleId).key
		
	def unlock(self):
		#if not self.isOpen():
		#	self.open('r+b')

		if not Titles.contains(self.titleId):
			raise IOError('No title key found in database!')

		self.ticket().setTitleKeyBlock(int(Titles.get(self.titleId).key, 16))
		Print.info('setting title key to ' + Titles.get(self.titleId).key)
		self.ticket().flush()
		self.close()
		self.hasValidTicket = True
		self.move()

	def setMasterKeyRev(self, newMasterKeyRev):
		if not Titles.contains(self.titleId):
			raise IOError('No title key found in database! ' + self.titleId)

		ticket = self.ticket()
		masterKeyRev = ticket.getMasterKeyRevision()
		titleKey = ticket.getTitleKeyBlock()
		newTitleKey = Keys.changeTitleKeyMasterKey(titleKey.to_bytes(16, byteorder='big'), Keys.getMasterKeyIndex(masterKeyRev), Keys.getMasterKeyIndex(newMasterKeyRev))
		rightsId = ticket.getRightsId()

		if rightsId != 0:
			raise IOError('please remove titlerights first')

		if (newMasterKeyRev == None and rightsId == 0) or masterKeyRev == newMasterKeyRev:
			Print.info('Nothing to do')
			return

		Print.info('rightsId =\t' + hex(rightsId))
		Print.info('titleKey =\t' + str(hx(titleKey.to_bytes(16, byteorder='big'))))
		Print.info('newTitleKey =\t' + str(hx(newTitleKey)))
		Print.info('masterKeyRev =\t' + hex(masterKeyRev))



		for nca in self:
			if type(nca) == Nca:
				if nca.header.getCryptoType2() != masterKeyRev:
					pass
					raise IOError('Mismatched masterKeyRevs!')

		ticket.setMasterKeyRevision(newMasterKeyRev)
		ticket.setRightsId((ticket.getRightsId() & 0xFFFFFFFFFFFFFFFF0000000000000000) + newMasterKeyRev)
		ticket.setTitleKeyBlock(int.from_bytes(newTitleKey, 'big'))

		for nca in self:
			if type(nca) == Nca:
				if nca.header.getCryptoType2() != newMasterKeyRev:
					Print.info('writing masterKeyRev for %s, %d -> %s' % (str(nca._path),  nca.header.getCryptoType2(), str(newMasterKeyRev)))

					encKeyBlock = nca.header.getKeyBlock()

					if sum(encKeyBlock) != 0:
						key = Keys.keyAreaKey(Keys.getMasterKeyIndex(masterKeyRev), nca.header.keyIndex)
						Print.info('decrypting with %s (%d, %d)' % (str(hx(key)), Keys.getMasterKeyIndex(masterKeyRev), nca.header.keyIndex))
						crypto = aes128.AESECB(key)
						decKeyBlock = crypto.decrypt(encKeyBlock)

						key = Keys.keyAreaKey(Keys.getMasterKeyIndex(newMasterKeyRev), nca.header.keyIndex)
						Print.info('encrypting with %s (%d, %d)' % (str(hx(key)), Keys.getMasterKeyIndex(newMasterKeyRev), nca.header.keyIndex))
						crypto = aes128.AESECB(key)

						reEncKeyBlock = crypto.encrypt(decKeyBlock)
						nca.header.setKeyBlock(reEncKeyBlock)


					if newMasterKeyRev >= 3:
						nca.header.setCryptoType(2)
						nca.header.setCryptoType2(newMasterKeyRev)
					else:
						nca.header.setCryptoType(newMasterKeyRev)
						nca.header.setCryptoType2(0)


	def removeTitleRights(self):
		if not Titles.contains(self.titleId):
			raise IOError('No title key found in database! ' + self.titleId)

		ticket = self.ticket()
		masterKeyRev = ticket.getMasterKeyRevision()
		titleKeyDec = Keys.decryptTitleKey(ticket.getTitleKeyBlock().to_bytes(16, byteorder='big'), Keys.getMasterKeyIndex(masterKeyRev))
		rightsId = ticket.getRightsId()

		Print.info('rightsId =\t' + hex(rightsId))
		Print.info('titleKeyDec =\t' + str(hx(titleKeyDec)))
		Print.info('masterKeyRev =\t' + hex(masterKeyRev))



		for nca in self:
			if type(nca) == Nca:
				if nca.header.getCryptoType2() != masterKeyRev:
					pass
					raise IOError('Mismatched masterKeyRevs!')


		ticket.setRightsId(0)

		for nca in self:
			if type(nca) == Nca:
				if nca.header.getRightsId() == 0:
					continue

				kek = Keys.keyAreaKey(Keys.getMasterKeyIndex(masterKeyRev), nca.header.keyIndex)
				Print.info('writing masterKeyRev for %s, %d' % (str(nca._path),  masterKeyRev))
				Print.info('kek =\t' + hx(kek).decode())
				crypto = aes128.AESECB(kek)

				encKeyBlock = crypto.encrypt(titleKeyDec * 4)
				nca.header.setRightsId(0)
				nca.header.setKeyBlock(encKeyBlock)
				Hex.dump(encKeyBlock)

	def setGameCard(self, isGameCard = False):
		if isGameCard:
			targetValue = 1
		else:
			targetValue = 0

		for nca in self:
			if type(nca) == Nca:
				if nca.header.getIsGameCard() == targetValue:
					continue

				Print.info('writing isGameCard for %s, %d' % (str(nca._path),  targetValue))
				nca.header.setIsGameCard(targetValue)
			
		
	def pack(self, files):
		if not self.path:
			return False
			
		Print.info('\tRepacking to NSP...')
		
		hd = self.generateHeader(files)
		
		totalSize = len(hd) + sum(os.path.getsize(file) for file in files)
		if os.path.exists(self.path) and os.path.getsize(self.path) == totalSize:
			Print.info('\t\tRepack %s is already complete!' % self.path)
			return
			
		t = tqdm(total=totalSize, unit='B', unit_scale=True, desc=os.path.basename(self.path), leave=False)
		
		t.write('\t\tWriting header...')
		outf = open(self.path, 'wb')
		outf.write(hd)
		t.update(len(hd))
		
		done = 0
		for file in files:
			t.write('\t\tAppending %s...' % os.path.basename(file))
			with open(file, 'rb') as inf:
				while True:
					buf = inf.read(4096)
					if not buf:
						break
					outf.write(buf)
					t.update(len(buf))
		t.close()
		
		Print.info('\t\tRepacked to %s!' % outf.name)
		outf.close()

	def generateHeader(self, files):
		filesNb = len(files)
		stringTable = '\x00'.join(os.path.basename(file) for file in files)
		headerSize = 0x10 + (filesNb)*0x18 + len(stringTable)
		remainder = 0x10 - headerSize%0x10
		headerSize += remainder
		
		fileSizes = [os.path.getsize(file) for file in files]
		fileOffsets = [sum(fileSizes[:n]) for n in range(filesNb)]
		
		fileNamesLengths = [len(os.path.basename(file))+1 for file in files] # +1 for the \x00
		stringTableOffsets = [sum(fileNamesLengths[:n]) for n in range(filesNb)]
		
		header =  b''
		header += b'PFS0'
		header += pk('<I', filesNb)
		header += pk('<I', len(stringTable)+remainder)
		header += b'\x00\x00\x00\x00'
		for n in range(filesNb):
			header += pk('<Q', fileOffsets[n])
			header += pk('<Q', fileSizes[n])
			header += pk('<I', stringTableOffsets[n])
			header += b'\x00\x00\x00\x00'
		header += stringTable.encode()
		header += remainder * b'\x00'
		
		return header

	def verifyKey(self, key):
		for f in self:
			if type(f) == Nca:
				pass

	def verify(self):
		success = True
		for f in self:
			if not isinstance(f, Nca):
				continue
			hash = str(f.sha256())

			if hash[0:16] != str(f._path)[0:16]:
				Print.error('BAD HASH %s = %s' % (str(f._path), str(f.sha256())))
				success = False

		return success
