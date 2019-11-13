import nsz.Fs
import nsz.Fs.Pfs0
import nsz.Fs.Nca
import nsz.Fs.Type
import traceback
import os
import glob
import re
from nsz.nut import Print


def ExtractHashes(gamePath):
	fileHashes = set()
	gamePath = os.path.abspath(gamePath)
	container = Fs.factory(gamePath)
	container.open(gamePath, 'rb')
	try:
		for nspf in container:
			if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.META:
				for section in nspf:
					if isinstance(section, Fs.Pfs0.Pfs0):
						Cnmt = section.getCnmt()
						for entry in Cnmt.contentEntries:
							fileHashes.add(entry.hash.hex())
	finally:
		container.close()
	
	return fileHashes


def ExtractTitleIDAndVersion(gamePath, parseCnmt):
	titleId = ""
	version = -1
	
	#If filename includes titleID this will speed up skipping existing files immensely.
	gameName = os.path.basename(gamePath)
	titleIdResult = re.search(r'0100[0-9A-Fa-f]{12}', gameName)
	if titleIdResult:
		titleId = titleIdResult.group()
		
	versionResult = re.search(r'\[v\d+\]', gameName)
	if versionResult:
		version = int(versionResult.group()[2:-1])
	
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
	elif not parseCnmt:
		return None
	
	gamePath = os.path.abspath(gamePath)
	container = Fs.factory(gamePath)
	container.open(gamePath, 'rb')
	try:
		for nspf in container:
			if isinstance(nspf, Fs.Nca.Nca) and nspf.header.contentType == Fs.Type.Content.META:
				for section in nspf:
					if isinstance(section, Fs.Pfs0.Pfs0):
						Cnmt = section.getCnmt()
						titleId = Cnmt.titleId
						version = Cnmt.version
	finally:
		container.close()
	
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
		
	return None


def CreateTargetDict(targetFolder, parseCnmt, extension):
	filesAtTarget = {}
	alreadyExists = {}
	for file in os.scandir(targetFolder):
		try:
			filePath = os.path.join(targetFolder, file)
			if file.name.endswith(extension):
				Print.infoNoNewline('Extract TitleID/Version: {0} '.format(file.name))
				filesAtTarget[file.name.lower()] = filePath
				(titleID, version) = ExtractTitleIDAndVersion(file, True)
				titleIDEntry = alreadyExists.get(titleID)
				if titleIDEntry == None:
					titleIDEntry = {version: {filePath}}
				elif not version in titleIDEntry:
					titleIDEntry.add({version: {filePath}})
				else:
					titleIDEntry[version].add(filePath)
				alreadyExists[titleID] = titleIDEntry
				Print.info('=> {0} {1}'.format(titleID, version))
		except BaseException as e:
			Print.info("")
			traceback.print_exc()
			Print.error('Error: ' + str(e))
	return(filesAtTarget, alreadyExists)


def AllowedToWriteOutfile(filePath, targetFileExtension, targetDict, removeOld, overwrite, parseCnmt):
	(filesAtTarget, alreadyExists) = targetDict
	extractedIdVersion = ExtractTitleIDAndVersion(filePath, parseCnmt)
	if extractedIdVersion == None:
		Print.error("Failed to extract TitleID/Version from filename {0}. Use -p to extract from Cnmt.".format(os.path.basename(filePath)))
		return fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite)
	(titleID, version) = extractedIdVersion
	
	if removeOld:
		titleIDEntry = alreadyExists.get(titleID)
		if not titleIDEntry == None:
			exitFlag = False
			for versionEntry in titleIDEntry:
				if versionEntry < titleIDEntry:
					for (fileName, filePath) in filesAtTarget:
						Print.info('Delete outdated version: {0}'.format(filePath))
						filesAtTarget.remove(os.path.basename(filePath).name.lower())
						os.remove(file)
				else:
					exitFlag = True
			if exitFlag:
				Print.info('{0} with a the same ID and newer version already exists in the output directory.\n'\
				'If you want to process it do not use --rm-old-version!'.format(os.path.basename(filePath)))
				return False
	
	titleIDEntry = alreadyExists.get(titleID)
	if not titleIDEntry == None:
		for versionEntry in titleIDEntry:
			if versionEntry == titleIDEntry:
				if overwrite:
					for (fileName, filePath) in filesAtTarget:
						Print.info('Delete dublicate: {0}'.format(filePath))
						filesAtTarget.remove(os.path.basename(filePath).name.lower())
						os.remove(filePath)
				else:
					Print.info('{0} with the same ID and version already exists in the output directory.\n'\
					'If you want to overwrite it use the -w parameter!'.format(os.path.basename(filePath)))
					return False
	
	return fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite)
	
	
def fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite):
	outFile = (os.path.splitext(os.path.basename(filePath))[0]+targetFileExtension).lower()
	filePath = filesAtTarget.get(outFile)
	
	if filePath == None:
		return True
	
	if overwrite:
		os.remove(filePath)
		return True
	
	Print.info('{0} with the same file name already exists in the output directory.\n'\
	'If you want to overwrite it use the -w parameter!'.format(os.path.basename(filePath)))
	return False


def delete_source_file(source_file_path):
	if os.path.exists(source_file_path):
		Print.info("Deleting source file {0}".format(source_file_path))
		os.remove(source_file_path)
	else:
		Print.warning("{0} was already removed.".format(source_file_path))
