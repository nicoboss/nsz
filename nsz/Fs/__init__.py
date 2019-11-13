import nsz.Fs.Nsp
import nsz.Fs.Xci
import nsz.Fs.Nca
import nsz.Fs.Nacp
import nsz.Fs.Ticket
import nsz.Fs.Cnmt
import nsz.Fs.File

def factory(name):
	if name.endswith('.xci'):
		f = Fs.Xci.Xci()
	elif name.endswith('.xcz'):
		f = Fs.Xci.Xci()
	elif name.endswith('.nsp'):
		f = Fs.Nsp.Nsp()
	elif name.endswith('.nsz'):
		f = Fs.Nsp.Nsp()
	elif name.endswith('.nsx'):
		f = Fs.Nsp.Nsp()
	elif name.endswith('.nca'):
		f =  Fs.Nca.Nca()
	elif name.endswith('.nacp'):
		f =  Fs.Nacp.Nacp()
	elif name.endswith('.tik'):
		f =  Fs.Ticket.Ticket()
	elif name.endswith('.cnmt'):
		f =  Fs.Cnmt.Cnmt()
	else:
		f = Fs.File.File()

	return f