import sys
import time
import json
from sys import argv
from nsz.ParseArguments import *
from traceback import print_exc

enableInfo = True
enableError = True
enableWarning = True
enableDebug = False
# Turning on machine output will convert all levels to JSON.
machineReadableOutput = False
lastProgress = ''

if len(argv) > 1:
	# We must re-parse the command line parameters here because this module
	# is re-imported in multiple modules which resets the variables each import.
	args = ParseArguments.parse()

	# Does the user want machine readable output?
	if (args.machine_readable):
		machineReadableOutput = True

def info(s, pleaseNoPrint = None):
	if pleaseNoPrint == None:
		if machineReadableOutput == False:
			sys.stdout.write(s + "\n")
	else:
		if machineReadableOutput == False:
			while pleaseNoPrint.value() > 0:
				time.sleep(0.01)
			pleaseNoPrint.increment()
			sys.stdout.write(s + "\n")
			sys.stdout.flush()
			pleaseNoPrint.decrement()

def error(errorCode, s):
	if machineReadableOutput:
		s = json.dumps({"error": s, "errorCode": errorCode, "warning": False})

	sys.stdout.write(s + "\n")

def warning(s):
	if machineReadableOutput:
		s = json.dumps({"error": False, "warning": s})

	sys.stdout.write(s + "\n")

def debug(s):
	if machineReadableOutput == False:
		sys.stdout.write(s + "\n")

def exception():
	if machineReadableOutput == False:
		print_exc()

def progress(job, s):
	global lastProgress

	if machineReadableOutput:
		s = json.dumps({"job": job, "data": s, "error": False, "warning": False})

		if s != lastProgress:
			sys.stdout.write(s + "\n")

			lastProgress = s
