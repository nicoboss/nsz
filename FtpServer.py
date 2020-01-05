import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.servers import FTPServer
from pyftpdlib.filesystems import AbstractedFS
from pyftpdlib.filesystems import FilesystemError


class VirtualFileOpener:
	closed = False
	offset = 0
	filesize = 1000
	def __init__(self, fileName, mode="r"):
		self.name = fileName
	def __enter__(self):
		return self
	def read(self, size = None):
		sizeToRead = min(size, self.filesize-self.offset)
		buffer = b'A'*sizeToRead
		self.offset += sizeToRead
		return buffer
	def tell(self):
		return self.offset
	def flush(self):
		pass
	def closed(self):
		return closed
	def close(self):
		self.closed = True
	def __exit__(self, exc_type, exc_value, traceback):
		self.closed = True

class VirtualFS(AbstractedFS):
	def __init__(self, root, cmd_channel):
		super(VirtualFS, self).__init__(root, cmd_channel)
		
	def listdir(self, path):
		return ["out.xci"]
		
	def listdirinfo(self, path):
		return self.listdir(path)
	
	def validpath(self, path):
		return True
	
	def stat(self, path):
		return os.stat_result((33279, 15199648742737957, 776870189, 1, 0, 0, 58, 1578230190, 1578230190, 1578230089))
		
	lstat = stat
	
	def isfile(self, path):
		return True
		
	def islink(self, path):
		return True
		
	def isdir(self, path):
		return True
		
	def getsize(self, path):
		return 1000
		
	def getmtime(self, path):
		return 1000
		
	def realpath(self, path):
		return path
		
	def lexists(self, path):
		print("Hi")
		return True
		
	def open(self, filename, mode):
		return VirtualFileOpener(filename, mode)
		
class VirtualHandler(FTPHandler):
	def __init__(self, conn, server, ioloop=None):
		super(VirtualHandler, self).__init__(conn, server, ioloop)

def main():
	# Instantiate a dummy authorizer for managing 'virtual' users
	authorizer = DummyAuthorizer()
	
	# Define a new anonymous user having read-only permissions
	authorizer.add_anonymous(os.getcwd())
	
	# Instantiate FTP handler class
	handler = VirtualHandler
	handler.abstracted_fs = VirtualFS
	handler.authorizer = authorizer
	
	# Define a customized banner (string returned when client connects)
	handler.banner = "pyftpdlib based ftpd ready."
	
	# Specify a masquerade address and the range of ports to use for
	# passive connections.  Decomment in case you're behind a NAT.
	# handler.masquerade_address = '151.25.42.11'
	handler.passive_ports = range(60000, 65535)
	
	# Instantiate FTP server class and listen on 0.0.0.0:2121
	address = ('127.0.0.1', 21)
	server = FTPServer(address, handler)
	
	# set a limit for connections
	server.max_cons = 256
	server.max_cons_per_ip = 32
	
	# start ftp server
	server.serve_forever()


if __name__ == '__main__':
    main()