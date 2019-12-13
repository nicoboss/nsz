from Fs import Pfs0, Nca, Type, factory
from traceback import print_exc
from os import scandir, remove
from pathlib import Path
from re import search
from nut import Print
from GameType import *

def ExtractHashes(gamePath):
	fileHashes = set()
	gamePath = str(Path(gamePath).resolve())
	container = factory(gamePath)
	container.open(gamePath, 'rb')
	if isXciXcz(gamePath):
		container = container.hfs0['secure']
	try:
		for nspf in container:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.META:
				for section in nspf:
					if isinstance(section, Pfs0.Pfs0):
						Cnmt = section.getCnmt()
						for entry in Cnmt.contentEntries:
							fileHashes.add(entry.hash.hex())
	finally:
		container.close()
	return fileHashes

def ExtractTitleIDAndVersion(gamePath, parseCnmt):
	titleId = ""
	version = -1
	gameName = Path(gamePath).name
	titleIdResult = search(r'0100[0-9A-Fa-f]{12}', gameName)
	if titleIdResult:
		titleId = titleIdResult.group()
	versionResult = search(r'\[v\d+\]', gameName)
	if versionResult:
		version = int(versionResult.group()[2:-1])
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
	elif not parseCnmt:
		return None
	gamePath = str(Path(gamePath).resolve())
	container = factory(gamePath)
	print(gamePath)
	container.open(gamePath, 'rb')
	if isXciXcz(gamePath):
		container = container.hfs0['secure']
	try:
		for nspf in container:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.META:
				for section in nspf:
					if isinstance(section, Pfs0.Pfs0):
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
	for file in scandir(targetFolder):
		try:
			filePath = Path(targetFolder).joinpath(file)
			if file.name.endswith(extension):
				Print.infoNoNewline('Extract TitleID/Version: {0} '.format(file.name))
				filesAtTarget[file.name.lower()] = filePath
				(titleID, version) = ExtractTitleIDAndVersion(file, True)
				titleIDEntry = alreadyExists.get(titleID)
				if titleIDEntry == None:
					titleIDEntry = {version: [filePath]}
				elif not version in titleIDEntry:
					titleIDEntry[version] = [filePath]
				else:
					titleIDEntry[version].append(filePath)
				alreadyExists[titleID] = titleIDEntry
				Print.info('=> {0} {1}'.format(titleID, version))
		except BaseException as e:
			Print.info("")
			print_exc()
			Print.error('Error: ' + str(e))
	return(filesAtTarget, alreadyExists)

def AllowedToWriteOutfile(filePath, targetFileExtension, targetDict, removeOld, overwrite, parseCnmt):
	(filesAtTarget, alreadyExists) = targetDict
	extractedIdVersion = ExtractTitleIDAndVersion(filePath, parseCnmt)
	if extractedIdVersion == None:
		Print.error("Failed to extract TitleID/Version from filename {0}. Use -p to extract from Cnmt.".format(Path(filePath).name))
		return fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite)
	(titleIDExtracted, versionExtracted) = extractedIdVersion
	titleIDEntry = alreadyExists.get(titleIDExtracted)

	if removeOld:
		if titleIDEntry != None:
			exitFlag = False
			for versionEntry in titleIDEntry.keys():
				print(versionEntry, versionExtracted)
				if versionEntry < versionExtracted:
					for delFilePath in titleIDEntry[versionEntry]:
						Print.info('Delete outdated version: {0}'.format(delFilePath))
						remove(delFilePath)
						del filesAtTarget[Path(delFilePath).name.lower()]
				else:
					exitFlag = True
			if exitFlag:
				Print.info('{0} with a the same ID and newer version already exists in the output directory.\n'\
				'If you want to process it do not use --rm-old-version!'.format(Path(filePath).name))
				return False

	
	if not titleIDEntry == None:
		for versionEntry in titleIDEntry:
			if versionEntry == titleIDEntry:
				if overwrite:
					for (fileName, filePath) in filesAtTarget: # NEEDS TO BE FIXED
						Print.info('Delete duplicate: {0}'.format(filePath))
						filesAtTarget.remove(Path(filePath).name.lower())
						remove(filePath)
				else:
					Print.info('{0} with the same ID and version already exists in the output directory.\n'\
					'If you want to overwrite it use the -w parameter!'.format(Path(filePath).name))
					return False
	
	return fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite)

def fileNameCheck(filePath, targetFileExtension, filesAtTarget, removeOld, overwrite):
	outFile = str(Path(changeExtension(filePath, targetFileExtension)).name).lower()
	filePath = filesAtTarget.get(outFile)
	if filePath == None:
		return True
	if overwrite:
		remove(filePath)
		return True
	Print.info('{0} with the same file name already exists in the output directory.\n'\
	'If you want to overwrite it use the -w parameter!'.format(Path(filePath).name))
	return False

def delete_source_file(source_file_path):
	if Path(source_file_path).exists():
		Print.info("Deleting source file {0}".format(source_file_path))
		remove(source_file_path)
	else:
		Print.warning("{0} was already removed.".format(source_file_path))