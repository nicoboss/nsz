import nsz.Fs.Nsp
import nsz.Fs.Xci
import nsz.Fs.Nca
import nsz.Fs.Nacp
import nsz.Fs.Ticket
import nsz.Fs.Cnmt
import nsz.Fs.File

def factory(name):
	if name.endswith('.xci'):
		f = nsz.Fs.Xci.Xci()
	elif name.endswith('.xcz'):
		f = nsz.Fs.Xci.Xci()
	elif name.endswith('.nsp'):
		f = nsz.Fs.Nsp.Nsp()
	elif name.endswith('.nsz'):
		f = nsz.Fs.Nsp.Nsp()
	elif name.endswith('.nsx'):
		f = nsz.Fs.Nsp.Nsp()
	elif name.endswith('.nca'):
		f =  nsz.Fs.Nca.Nca()
	elif name.endswith('.nacp'):
		f =  nsz.Fs.Nacp.Nacp()
	elif name.endswith('.tik'):
		f =  nsz.Fs.Ticket.Ticket()
	elif name.endswith('.cnmt'):
		f =  nsz.Fs.Cnmt.Cnmt()
	else:
		f = nsz.Fs.File.File()

	return f