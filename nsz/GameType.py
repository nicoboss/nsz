from pathlib import Path

def isGame(filePath):
	return filePath.endswith('.nsp') or filePath.endswith('.xci') or filePath.endswith('.nsz') or filePath.endswith('.xcz')

def isUncompressedGame(filePath):
	return filePath.endswith('.nsp') or filePath.endswith('.xci')

def isCompressedGame(filePath):
	return filePath.endswith('.nsz') or filePath.endswith('.xcz')

def isNspNsz(filePath):
	return filePath.endswith('.nsp') or filePath.endswith('.nsz')

def isXciXcz(filePath):
	return filePath.endswith('.xci') or filePath.endswith('.xcz')

def getExtension(filePath):
	return Path(filePath).suffix

def getBasename(filePath):
	return Path(filePath).stem

def changeExtension(filePath, newExtension):
	filePathObj = Path(filePath)
	return filePathObj.parent.resolve().joinpath(filePathObj.stem + newExtension)

def getExtensionName(filePath):
	return Path(filePath).suffix[1:].upper()
