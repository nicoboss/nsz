from nsz.nut import aes128
from nsz.nut import Hex
from binascii import hexlify as hx, unhexlify as uhx
from struct import pack as pk, unpack as upk
from nsz.Fs.File import File, MemoryFile
from hashlib import sha256
import os
import re
import pathlib
from nsz.nut import Keys, Print

MEDIA_SIZE = 0x200



class Header(File):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1, nca = None):
		self.size = 0
		self.offset = 0
		self.nca = nca
		self.bktr_offset = 0
		self.bktr_size = 0
		self.magic = None
		self.version = None
		self.enctryCount = 0
		self.reserved = None
		self.buffer = None
		super(Header, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)

	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Header, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		self.rewind()

		self.bktr_offset = self.readInt64()
		self.bktr_size = self.readInt64()
		self.magic = self.read(0x4)
		self.version = self.readInt32()
		self.enctryCount = self.readInt32()
		self.reserved = self.readInt32()

	def printInfo(self, maxDepth = 3, indent = 0):
		if not self.bktr_size:
			return

		tabs = '\t' * indent
		Print.info('\n%sBKTR' % (tabs))
		Print.info('%soffset = %d' % (tabs, self.bktr_offset))
		Print.info('%ssize = %d' % (tabs, self.bktr_size))
		Print.info('%sentry count = %d' % (tabs, self.enctryCount))
		
		Print.info('\n')

class BktrRelocationEntry:
	def __init__(self, f):
		self.virtualOffset = f.readInt64()
		self.physicalOffset = f.readInt64()
		self.isPatch = f.readInt32()
		
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('%sRelocation Entry %s %x = %x' % (tabs, 'Patch' if self.isPatch else 'Base', self.physicalOffset, self.virtualOffset))
		
class BktrSubsectionEntry:
	def __init__(self, f):
		self.virtualOffset = f.readInt64()
		self.size = 0
		self.padding = f.readInt32()
		self.ctr = f.readInt32()
		
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('%sSubsection Entry %d, CTR = %x' % (tabs, self.virtualOffset, self.ctr))
		
class BktrBucket:
	def __init__(self, f):
		self.padding = f.readInt32()
		self.entryCount = f.readInt32()
		self.endOffset = f.readInt64()
		self.entries = []
		
	def getEntry(self, offset):
		index = 0
		last = self.entries[index]
		for entry in self.entries:
			if entry.virtualOffset > offset:
				break
				
			last = self.entries[index]
			index += 1
			
		return last

			
	def printInfo(self, maxDepth = 3, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sBKTR Bucket' % tabs)
		Print.info('%sentries: %d' % (tabs, self.entryCount))
		Print.info('%send offset: %d' % (tabs, self.endOffset))
		
		for entry in self.entries:
			entry.printInfo(maxDepth, indent + 1)
			
class BktrSubsectionBucket(BktrBucket):
	def __init__(self, f):
		super(BktrSubsectionBucket, self).__init__(f)
		
		for i in range(self.entryCount):
			self.entries.append(BktrSubsectionEntry(f))
			
			
class BktrRelocationBucket(BktrBucket):
	def __init__(self, f):
		super(BktrRelocationBucket, self).__init__(f)
		
		if self.entryCount > 0xFFFF:
			raise IOError('Too many entries')
			
		for i in range(self.entryCount):
			self.entries.append(BktrRelocationEntry(f))
			
		
class Bktr(Header):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1, nca = None):
		self.basePhysicalOffsets  = []
		super(Bktr, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter, nca)
		
		
	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Bktr, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		
		if self.bktr_size:
			self.nca.seek(self.bktr_offset)
			self.nca.readInt32() # padding
			self.bucketCount = self.nca.readInt32()
			self.totalPatchImageSize = self.nca.readInt64()
			self.basePhysicalOffsets = []
			for i in range(int(0x3FF0 / 8)):
				self.basePhysicalOffsets.append(self.nca.readInt64())
				
	def isValid(self):
		return True if self.bktr_size > 0 else False
				
	def getBucket(self, offset):
		if len(self.buckets) == 0:
			return None
			
		index = 0
		last = self.buckets[0]
		
		for virtualOffset in self.basePhysicalOffsets:
			if index >= len(self.buckets):
				break
				
			if offset > virtualOffset:
				break
				
			last = self.buckets[index]
			index += 1
			
		return last

	def printInfo(self, maxDepth = 3, indent = 0):
		super(Bktr, self).printInfo(maxDepth, indent)
		tabs = '\t' * indent
		Print.info('%sOffsets' % (tabs))
		
		i = 0
		for off in self.basePhysicalOffsets:
			i += 1
			if off == 0 and i != 1:
				break
			Print.info('%s %x' % (tabs, off))
		

		
class Bktr1(Bktr):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1, nca = None):
		self.buckets = []
		super(Bktr1, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter, nca)
		
	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Bktr1, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
		
		self.buckets = []
		
		#if self.bktr_size:
		#	for i in range(self.bucketCount):
		#		self.buckets.append(BktrRelocationBucket(self.nca))
				
	def getRelocationEntry(self, offset):
		if len(self.buckets) == 0:
			return None

		bucket = self.buckets[0]		

		index = 0
		for virtualOffset in self.basePhysicalOffsets:

			if virtualOffset > offset or index >= len(self.buckets):
				break

			bucket = self.buckets[index]
			index += 1
			
		result = bucket.entries[0]
		for entry in bucket.entries:
			if offset > entry.virtualOffset:
				break
			result = entry
			
		return entry
			
		
	def printInfo(self, maxDepth = 3, indent = 0):
		super(Bktr1, self).printInfo(maxDepth, indent)
		tabs = '\t' * indent

		for bucket in self.buckets:
			bucket.printInfo(maxDepth, indent+1)
		
class Bktr2(Bktr):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1, nca = None):
		self.buckets = []
		super(Bktr2, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter, nca)
		
	def open(self, file = None, mode = 'rb', cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Bktr2, self).open(file, mode, cryptoType, cryptoKey, cryptoCounter)
	
		self.buckets = []
		
		if self.bktr_size:
			for i in range(self.bucketCount):
				self.buckets.append(BktrSubsectionBucket(self.nca))
		
	def getEntries(self, offset, size):
		entries = []
		
		bucket = self.getBucket(offset)
		if bucket is not None:
			entries.append(bucket.getEntry(offset))		
		
		return entries
		
	def getAllEntries(self):
		entries = []

		for bucket in self.buckets:
			last = None
			for entry in bucket.entries:
				if last is not None:
					last.size = entry.virtualOffset - last.virtualOffset
				last = entry
				entries.append(entry)
				
			if len(entries) != 0:
				entries[-1].size = bucket.endOffset - entries[-1].virtualOffset
		
		return entries
		
	def printInfo(self, maxDepth = 3, indent = 0):
		super(Bktr2, self).printInfo(maxDepth, indent)

		for bucket in self.buckets:
			bucket.printInfo(maxDepth, indent+1)

		