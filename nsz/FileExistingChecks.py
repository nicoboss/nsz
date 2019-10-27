import Fs
import Fs.Pfs0
import Fs.Nca
import Fs.Type
import os
import glob
import re
from nut import Print

def ExtractTitleIDAndVersion(gamePath):
	titleId = ""
	version = -1
	gameName = os.path.basename(gamePath)
	titleIdResult = re.search(r'0100[0-9A-Fa-f]{12}', gameName)
	if titleIdResult:
		titleId = titleIdResult.group()
		
	versionResult = re.search(r'\[v\d+\]', gameName)
	if versionResult:
		version = int(versionResult.group()[2:-1])
	
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
	
	gamePath = os.path.abspath(gamePath)
	container = Fs.factory(gamePath)
	container.open(gamePath, 'rb')
	for nspf in container:
		if isinstance(nspf, Fs.Ticket.Ticket):
			titleId = nspf.getRightsId()
		if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.META:
			for section in nspf:
				if isinstance(section, Fs.Pfs0.Pfs0):
					version = section.getVersion()
	
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
		
	raise("Failed to determinate TitleID/Version!")


def AllowedToWriteOutfile(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite):
	print(ExtractTitleIDAndVersion(filePath))
	# If filename includes titleID this will speed up skipping existing files immensely.
	outFile = (os.path.splitext(os.path.basename(filePath))[0]+targetFileExtension).lower()
	if not overwrite and outFile in filesAtTarget:
		Print.info('{0} with the same file name already exists in the output directory.\n'\
		'If you want to overwrite it use the -w parameter!'.format(filePath))
		return False
	
	return True
	
	
	
	titleIdResult = re.search(r'0100[0-9A-Fa-f]{12}', filePath)
	if not titleIdResult:
		return True
	titleId = titleIdResult.group()
	
	versionResult = re.search(r'\[v\d+\]', filePath)
	potentiallyExistingFile = ''
	if versionResult:
		versionNumber = int(versionResult.group()[2:-1])
		for file in filesAtTarget:
			if re.match(r'.*%s.*\[v%s\]\%s' % (titleId, versionNumber, targetFileExtension), file, re.IGNORECASE):
				potentiallyExistingFile = file
				break
			elif re.match(r'.*%s.*\%s' % (titleId, targetFileExtension), file, re.IGNORECASE):
				targetVersionResult = re.search(r'\[v\d+\]',file)
				if targetVersionResult:
					targetVersionNumber = int(targetVersionResult.group()[2:-1])
					Print.info('Target Version: {0}'.format(targetVersionNumber))
					if targetVersionNumber < versionNumber:
						Print.info('Target file is an old update')
						if removeOld:
							Print.info('Deleting old update of the file...')
							os.remove(file)

	if not overwrite:
		# While we could also move filename check here, it doesn't matter much, because
		# we check filename without reading anything from nsp/nsz so it's fast enough
		if potentiallyExistingFile:
			potentiallyExistingFileName = os.path.basename(potentiallyExistingFile)
			Print.info('{0} with the same title ID {1} but a different filename already exists in the output directory.\n'\
			'If you want to continue with {2} keeping both files use the -w parameter!'
			.format(potentiallyExistingFileName, titleId, potentiallyExistingFile))
			return False
	return True
