from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from nsz.Fs.File import File
from hashlib import sha256
from nsz import Fs
import os
import re
import pathlib
from nsz.nut import Keys
from nsz.nut import Print
from nsz.Fs.Pfs0 import Pfs0
from nsz.Fs.Ticket import Ticket
from nsz.Fs.Nca import Nca
import enlighten
import shutil
from nsz.nut import Titles
from nsz.nut.Titles import Title
from nsz.PathTools import *

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

	def unpack(self, path, extractregex=r"*"):
		os.makedirs(str(path), exist_ok=True)

		for nspf in self:
			filePath_str = str(path.joinpath(nspf._path))
			if not re.match(extractregex, filePath_str):
				continue
			f = open(filePath_str, 'wb')
			nspf.rewind()
			i = 0

			pageSize = 0x100000

			while True:
				buf = nspf.read(pageSize)
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
		if re.match(r'[A-F0-9]{16}', id, re.I):
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

		z = re.match(r'.*\[([a-zA-Z0-9]{16})\].*', path, re.I)
		if z:
			self.titleId = z.groups()[0].upper()
		else:
			Print.info('could not get title id from filename, name needs to contain [titleId] : ' + path)
			self.titleId = None

		z = re.match(r'.*\[v([0-9]+)\].*', path, re.I)

		if z:
			self.version = z.groups()[0]

		if path.endswith('.nsp'):
			if self.hasValidTicket is None:
				self.setHasValidTicket(True)
		elif path.endswith('.nsx'):
			if self.hasValidTicket is None:
				self.setHasValidTicket(False)
		else:
			Print.info('unknown extension ' + str(path))
			return

	def getPath(self):
		return self.path or ''

	def open(self, path = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Nsp, self).open(path or self.path, mode, cryptoType, cryptoKey, cryptoCounter)

		return True

	def cleanFilename(self, s):
		if s is None:
			return ''
		#s = re.sub(r'\s+\Demo\s*', ' ', s, re.I)
		s = re.sub(r'\s*\[DLC\]\s*', '', s, re.I)
		s = re.sub(r'[\/\\\:\*\?\"\<\>\|\.\s™©®()\~]+', ' ', s)
		return s.strip()

	def dict(self):
		return {"titleId": self.titleId, "hasValidTicket": self.hasValidTicket, 'extractedNcaMeta': self.getExtractedNcaMeta(), 'version': self.version, 'timestamp': self.timestamp, 'path': self.path }

	def ticket(self):
		for f in (f for f in self if type(f) == Ticket):
			return f
		self.ticketless = True
		# Exception suppressed to allow compress/decompress of ticketless -single base game or multicontent- dump files.
		#raise IOError('no ticket in NSP')

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


	def pack(self, files, fix_padding):
		if not self.path:
			return False

		Print.info('\tRepacking to NSP...')

		hd = self.generateHeader(files, fix_padding)

		totalSize = len(hd) + sum(os.path.getsize(file) for file in files)
		if os.path.exists(self.path) and os.path.getsize(self.path) == totalSize:
			Print.info('\t\tRepack %s is already complete!' % self.path)
			return

		t = enlighten.Counter(total=totalSize, unit='B', desc=os.path.basename(self.path), leave=False)

		Print.info('\t\tWriting header...')
		outf = open(self.path, 'wb')
		outf.write(hd)
		t.update(len(hd))

		done = 0
		for f_str in files:
			for filePath in expandFiles(Path(f_str)):
				Print.info('\t\tAppending %s...' % os.path.basename(filePath))
				with open(filePath, 'rb') as inf:
					while True:
						buf = inf.read(4096)
						if not buf:
							break
						outf.write(buf)
						t.update(len(buf))
		t.close()

		Print.info('\t\tRepacked to %s!' % outf.name)
		outf.close()

	def generateHeader(self, files, fix_padding):
		filesNb = len(files)
		stringTable = '\x00'.join(os.path.basename(file) for file in files)
		headerSize = 0x10 + (filesNb)*0x18 + len(stringTable)
		if fix_padding:
			paddingSize = (16 - headerSize % 16) % 16
			stringTable += '\x00' * paddingSize
			headerSize = 0x10 + (filesNb)*0x18 + len(stringTable)

		fileSizes = [os.path.getsize(file) for file in files]
		fileOffsets = [sum(fileSizes[:n]) for n in range(filesNb)]

		fileNamesLengths = [len(os.path.basename(file))+1 for file in files] # +1 for the \x00
		stringTableOffsets = [sum(fileNamesLengths[:n]) for n in range(filesNb)]

		header =  b''
		header += b'PFS0'
		header += pk('<I', filesNb)
		header += pk('<I', len(stringTable))
		header += b'\x00\x00\x00\x00'
		for n in range(filesNb):
			header += pk('<Q', fileOffsets[n])
			header += pk('<Q', fileSizes[n])
			header += pk('<I', stringTableOffsets[n])
			header += b'\x00\x00\x00\x00'
		header += stringTable.encode()

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
				Print.error(600, 'BAD HASH %s = %s' % (str(f._path), str(f.sha256())))
				success = False

		return success
