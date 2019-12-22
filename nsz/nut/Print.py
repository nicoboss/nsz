import sys
import time

global silent
enableInfo = True
enableError = True
enableWarning = True
enableDebug = False

silent = False
	
def info(s, pleaseNoPrint = None):
	if pleaseNoPrint == None:
		sys.stdout.write(s + "\n")
	else:
		while pleaseNoPrint.value() > 0:
			#print("Wait")
			time.sleep(0.01)
		pleaseNoPrint.increment()
		sys.stdout.write(s + "\n")
		sys.stdout.flush()
		pleaseNoPrint.decrement()
	
def infoNoNewline(s):
	sys.stdout.write(s)

def error(s):
	sys.stdout.write(s + "\n")

def warning(s):
	sys.stdout.write(s + "\n")

def debug(s):
	sys.stdout.write(s + "\n")
