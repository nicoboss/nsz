from . import Nsp
from . import Xci
from . import Nca
from . import Nacp
from . import Ticket
from . import Cnmt
from . import File

def factory(name):
	if name.endswith('.xci'):
		f = Xci.Xci()
	elif name.endswith('.xcz'):
		f = Xci.Xci()
	elif name.endswith('.nsp'):
		f = Nsp.Nsp()
	elif name.endswith('.nsz'):
		f = Nsp.Nsp()
	elif name.endswith('.nsx'):
		f = Nsp.Nsp()
	elif name.endswith('.nca'):
		f = Nca.Nca()
	elif name.endswith('.nacp'):
		f = Nacp.Nacp()
	elif name.endswith('.tik'):
		f = Ticket.Ticket()
	elif name.endswith('.cnmt'):
		f = Cnmt.Cnmt()
	else:
		f = File.File()

	return f