import sys
import zstandard
from Crypto.Cipher import AES
from Crypto.Util import Counter
from binascii import hexlify as hx, unhexlify as uhx

if len(sys.argv) < 3:
	print('usage: decompress.py input.ncz output.nca')

def readInt64(f, byteorder='little', signed = False):
		return int.from_bytes(f.read(8), byteorder=byteorder, signed=signed)

def readInt128(f, byteorder='little', signed = False):
	return int.from_bytes(f.read(16), byteorder=byteorder, signed=signed)

class AESCTR:
	def __init__(self, key, nonce, offset = 0):
		self.key = key
		self.nonce = nonce
		self.seek(offset)

	def encrypt(self, data, ctr=None):
		if ctr is None:
			ctr = self.ctr
		return self.aes.encrypt(data)

	def decrypt(self, data, ctr=None):
		return self.encrypt(data, ctr)

	def seek(self, offset):
		self.ctr = Counter.new(64, prefix=self.nonce[0:8], initial_value=(offset >> 4))
		self.aes = AES.new(self.key, AES.MODE_CTR, counter=self.ctr)
		
class Section:
	def __init__(self, f):
		self.f = f
		self.offset = readInt64(f)
		self.size = readInt64(f)
		self.cryptoType = readInt64(f)
		readInt64(f) # padding
		self.cryptoKey = f.read(16)
		self.cryptoCounter = f.read(16)

with open(sys.argv[1], 'rb') as f:
	header = f.read(0x4000)
	magic = readInt64(f)
	sectionCount = readInt64(f)
	sections = []
	for i in range(sectionCount):
		sections.append(Section(f))
		
	dctx = zstandard.ZstdDecompressor()
	reader = dctx.stream_reader(f)
		
	with open(sys.argv[2], 'wb+') as o:
		o.write(header)
		
		while True:
			chunk = reader.read(16384)
			
			if not chunk:
				break
				
			o.write(chunk)
			
		for s in sections:
			if s.cryptoType == 1: #plain text
				continue
				
			if s.cryptoType not in (3, 4):
				raise IOError('unknown crypto type: %d' % s.cryptoType)
				
			print('%x - %d bytes, type %d, key: %s, iv: %s' % (s.offset, s.size, s.cryptoType, str(hx(s.cryptoKey)), str(hx(s.cryptoCounter))))
			
			i = s.offset
			
			crypto = AESCTR(s.cryptoKey, s.cryptoCounter)
			end = s.offset + s.size
			
			while i < end:
				o.seek(i)
				crypto.seek(i)
				chunkSz = 0x10000 if end - i > 0x10000 else end - i
				buf = o.read(chunkSz)
				
				if not len(buf):
					break
				
				o.seek(i)
				o.write(crypto.encrypt(buf))
				
				i += chunkSz
			
			
			