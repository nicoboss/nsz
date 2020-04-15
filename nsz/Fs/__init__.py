import nsz.Fs.Nsp
import nsz.Fs.Xci
import nsz.Fs.Nca
import nsz.Fs.Nacp
import nsz.Fs.Ticket
import nsz.Fs.Cnmt
import nsz.Fs.File

def factory(name):
	if name.suffix == '.xci':
		f = nsz.Fs.Xci.Xci()
	elif name.suffix == '.xcz':
		f = nsz.Fs.Xci.Xci()
	elif name.suffix == '.nsp':
		f = nsz.Fs.Nsp.Nsp()
	elif name.suffix == '.nsz':
		f = nsz.Fs.Nsp.Nsp()
	elif name.suffix == '.nspz':
		f = nsz.Fs.Nsp.Nsp()
	elif name.suffix == '.nsx':
		f = nsz.Fs.Nsp.Nsp()
	elif name.suffix == '.nca':
		f = nsz.Fs.Nca.Nca()
	elif name.suffix == '.ncz':
		f = nsz.Fs.File.File()
	elif name.suffix == '.nacp':
		f = nsz.Fs.Nacp.Nacp()
	elif name.suffix == '.tik':
		f = nsz.Fs.Ticket.Ticket()
	elif name.suffix == '.cnmt':
		f = nsz.Fs.Cnmt.Cnmt()
	elif str(name) in set(['normal', 'logo', 'update', 'secure']):
		f = nsz.Fs.Hfs0.Hfs0(None)
	else:
		f = nsz.Fs.File.File()

	return f