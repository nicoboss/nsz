
global silent
enableInfo = True
enableError = True
enableWarning = True
enableDebug = False

silent = False


def info(s):
	print(s)
	
def infoNoNewline(s):
	print(s, end = '')

def error(s):
	print(s)

def warning(s):
	print(s)

def debug(s):
	print(s)
