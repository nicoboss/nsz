import sys
import time
import json
from sys import argv
from multiprocessing.process import current_process
from nsz.ParseArguments import *
from traceback import print_exc

enableInfo = True
enableError = True
enableWarning = True
enableDebug = False
silent = False
# Turning on machine output will convert all levels to JSON.
machineReadableOutput = False
minimalOutput = False
lastProgress = ''
lastMinimalProgress = ''
lastMinimalProgressLength = 0
spinnerFrames = ['|', '/', '-', '\\']
spinnerIndex = 0

if len(argv) > 1:
	# We must re-parse the command line parameters here because this module
	# is re-imported in multiple modules which resets the variables each import.
	args = ParseArguments.parse()

	# Does the user want machine readable output?
	if (args.machine_readable):
		machineReadableOutput = True

	# Minimal output suppresses normal info logs. Errors and warnings are kept.
	if (args.minimal_output):
		minimalOutput = True
		enableInfo = False

def info(s, pleaseNoPrint = None):
	if silent or not enableInfo:
		return
	
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
	if silent or not enableError:
		return
	if machineReadableOutput:
		s = json.dumps({"error": s, "errorCode": errorCode, "warning": False})

	sys.stdout.write(s + "\n")

def warning(s):
	if silent or not enableWarning:
		return
	if machineReadableOutput:
		s = json.dumps({"error": False, "warning": s})

	sys.stdout.write(s + "\n")

def debug(s):
	if silent or not enableDebug:
		return
	if machineReadableOutput == False:
		sys.stdout.write(s + "\n")

def exception():
	if machineReadableOutput == False:
		print_exc()

def progress(job, s):
	global lastProgress
	global lastMinimalProgress
	global lastMinimalProgressLength
	global spinnerIndex

	if machineReadableOutput:
		s = json.dumps({"job": job, "data": s, "error": False, "warning": False})

		if s != lastProgress:
			sys.stdout.write(s + "\n")

			lastProgress = s
		return

	if minimalOutput:
		# Keep minimal output stable by avoiding worker-process duplicates.
		if current_process().name != 'MainProcess':
			return
		if job == 'Complete':
			minimalLine = '100% Done'
		elif isinstance(s, dict) and 'sourceSize' in s and 'processed' in s:
			total = s['sourceSize']
			processed = s['processed']
			percentage = 0 if total <= 0 else min(100, int(processed * 100 / total))
			step = s['step'] if 'step' in s else job
			spinner = spinnerFrames[spinnerIndex]
			spinnerIndex = (spinnerIndex + 1) % len(spinnerFrames)
			minimalLine = f'{spinner} {percentage}% {step}'
		else:
			return
		if job != 'Complete' or minimalLine != lastMinimalProgress:
			padding = ''
			if lastMinimalProgressLength > len(minimalLine):
				padding = ' ' * (lastMinimalProgressLength - len(minimalLine))
			if job == 'Complete':
				sys.stdout.write('\r' + minimalLine + padding + '\n')
				lastMinimalProgressLength = 0
				lastMinimalProgress = ''
			else:
				sys.stdout.write('\r' + minimalLine + padding)
				lastMinimalProgressLength = len(minimalLine)
				lastMinimalProgress = minimalLine
			sys.stdout.flush()

def isMinimalOutput():
	return minimalOutput
