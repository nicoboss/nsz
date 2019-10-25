import os
import glob
import re
from nut import Print

def AllowedToWriteOutfile(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite):
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
