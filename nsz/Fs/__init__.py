import Fs.Nsp
import Fs.Xci
import Fs.Nca
import Fs.Nacp
import Fs.Ticket
import Fs.Cnmt
import Fs.File

def factory(name):
	if name.suffix == '.xci':
		f = Fs.Xci.Xci()
	elif name.suffix == '.xcz':
		f = Fs.Xci.Xci()
	elif name.suffix == '.nsp':
		f = Fs.Nsp.Nsp()
	elif name.suffix == '.nsz':
		f = Fs.Nsp.Nsp()
	elif name.suffix == '.nspz':
		f = Fs.Nsp.Nsp()
	elif name.suffix == '.nsx':
		f = Fs.Nsp.Nsp()
	elif name.suffix == '.nca':
		f = Fs.Nca.Nca()
	elif name.suffix == '.ncz':
		f = Fs.File.File()
	elif name.suffix == '.nacp':
		f = Fs.Nacp.Nacp()
	elif name.suffix == '.tik':
		f = Fs.Ticket.Ticket()
	elif name.suffix == '.cnmt':
		f = Fs.Cnmt.Cnmt()
	elif str(name) in set(['normal', 'logo', 'update', 'secure']):
		f = Fs.Hfs0.Hfs0(None)
	else:
		f = Fs.File.File()

	return f