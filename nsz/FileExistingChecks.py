from nsz.Fs import Pfs0, Nca, Type, factory
from traceback import print_exc
from os import scandir, remove
from pathlib import Path
from re import search
from nsz.nut import Print
from nsz.PathTools import *
import os

def ExtractHashes(container):
	fileHashes = set()
	for nspf in container:
		if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.META:
			for section in nspf:
				if isinstance(section, Pfs0.Pfs0):
					Cnmt = section.getCnmt()
					for entry in Cnmt.contentEntries:
						fileHashes.add(entry.hash.hex())
	return fileHashes

def ExtractTitleIDAndVersion(gamePath, args = None):
	titleId = ""
	version = -1
	gameName = Path(gamePath).name
	titleIdResult = search(r'0100[0-9A-Fa-f]{12}', gameName)
	if args == None or not args.alwaysParseCnmt:
		if titleIdResult:
			titleId = titleIdResult.group().upper()
		versionResult = search(r'\[v\d+\]', gameName)
		if versionResult:
			version = int(versionResult.group()[2:-1])
		if titleId != "" and version > -1 and version%65536 == 0:
			return(titleId, version)
		elif args != None and not args.parseCnmt:
			return None
	gamePath = Path(gamePath).resolve()
	container = factory(gamePath)
	container.open(str(gamePath), 'rb')
	if isXciXcz(gamePath):
		container = container.hfs0['secure']
	try:
		for nspf in container:
			if isinstance(nspf, Nca.Nca) and nspf.header.contentType == Type.Content.META:
				for section in nspf:
					if isinstance(section, Pfs0.Pfs0):
						Cnmt = section.getCnmt()
						titleId = Cnmt.titleId.upper()
						version = Cnmt.version
	finally:
		container.close()
	if titleId != "" and version > -1 and version%65536 == 0:
		return(titleId, version)
	return None

def CreateTargetDict(targetFolder, args, extension, filesAtTarget = {}, alreadyExists = {}):
	for filePath in expandFiles(targetFolder):
		try:
			filePath_str = str(filePath)
			if (isGame(filePath) or filePath.suffix == ".nspz" or filePath.suffix == ".nsx") and (extension == None or filePath.suffix == extension):
				print(filePath)
				Print.infoNoNewline('Extract TitleID/Version: {0} '.format(filePath.name))
				filesAtTarget[filePath.name.lower()] = filePath_str
				extractedIdVersion = ExtractTitleIDAndVersion(filePath, args)
				if extractedIdVersion == None:
					if args.parseCnmt or args.alwaysParseCnmt:
						Print.error('Failed to extract TitleID/Version from booth filename "{0}" and Cnmt - Outdated keys.txt?'.format(Path(filePath).name))
					else:
						Print.error('Failed to extract TitleID/Version from filename "{0}". Use -p to extract from Cnmt.'.format(Path(filePath).name))
					continue
				titleID, version = extractedIdVersion
				titleIDEntry = alreadyExists.get(titleID)
				if titleIDEntry == None:
					titleIDEntry = {version: [filePath_str]}
				elif not version in titleIDEntry:
					titleIDEntry[version] = [filePath_str]
				else:
					titleIDEntry[version].append(filePath_str)
				alreadyExists[titleID] = titleIDEntry
				Print.info('=> {0} {1}'.format(titleID, version))
		except BaseException as e:
			Print.info("")
			print_exc()
			Print.error('Error: ' + str(e))
	return(filesAtTarget, alreadyExists)

def AllowedToWriteOutfile(filePath, targetFileExtension, targetDict, args):
	(filesAtTarget, alreadyExists) = targetDict
	extractedIdVersion = ExtractTitleIDAndVersion(filePath, args)
	if extractedIdVersion == None:
		if args.parseCnmt or args.alwaysParseCnmt:
			Print.error('Failed to extract TitleID/Version from booth filename "{0}" and Cnmt - Outdated keys.txt?'.format(Path(filePath).name))
		else:
			Print.error('Failed to extract TitleID/Version from filename "{0}". Use -p to extract from Cnmt.'.format(Path(filePath).name))
		return fileNameCheck(filePath, targetFileExtension, filesAtTarget, args.rm_old_version, args.overwrite)
	(titleIDExtracted, versionExtracted) = extractedIdVersion
	titleIDEntry = alreadyExists.get(titleIDExtracted)

	if titleIDEntry != None:
		DuplicateEntriesToDelete = []
		OutdatedEntriesToDelete = []
		exitFlag = False
		for versionEntry in titleIDEntry.keys():
			if versionEntry == versionExtracted:
				if args.overwrite:
					DuplicateEntriesToDelete.append(versionEntry)
				else:
					Print.info('{0} with the same ID and version already exists in the output directory.\n'\
					'If you want to overwrite it use the -w parameter!'.format(titleIDEntry[versionEntry]))
					return False
			elif versionEntry < versionExtracted:
				if args.rm_old_version:
					OutdatedEntriesToDelete.append(versionEntry)
			else: #versionEntry > versionExtracted
				if args.rm_old_version:
					exitFlag = True
		if exitFlag:
			Print.info('{0} with a the same ID and newer version already exists in the output directory.\n'\
			'If you want to process it do not use --rm-old-version!'.format(titleIDEntry[versionEntry]))
			return False
		
		for versionEntry in DuplicateEntriesToDelete:
			for delFilePath in titleIDEntry[versionEntry]:
				Print.info('Delete duplicate: {0}'.format(delFilePath))
				remove(delFilePath)
				del filesAtTarget[Path(delFilePath).name.lower()]
			del titleIDEntry[versionEntry]
		for versionEntry in OutdatedEntriesToDelete:
			for delFilePath in titleIDEntry[versionEntry]:
				Print.info('Delete outdated version: {0}'.format(delFilePath))
				remove(delFilePath)
				del filesAtTarget[Path(delFilePath).name.lower()]
			del titleIDEntry[versionEntry]
	
	return fileNameCheck(filePath, targetFileExtension, filesAtTarget, args.rm_old_version, args.overwrite)

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

def delete_source_file(source_file_path, outFolder):
	filePath = Path(source_file_path)
	if filePath.exists():
		resultFile = Path(targetExtension(outFolder.joinpath(filePath.name)))
		if resultFile.exists():
			Print.info("[DELETING]   Source file {0}".format(source_file_path))
			remove(source_file_path)
		else:
			Print.warning("[WARNING]    Skipped deleting source file because target file doesn't exist")
	else:
		Print.warning("[WARNING]    {0} was already removed.".format(source_file_path))
