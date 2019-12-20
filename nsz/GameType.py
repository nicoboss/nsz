from pathlib import Path

def isGame(filePath):
	return filePath.suffix == '.nsp' or filePath.suffix == '.xci' or filePath.suffix == '.nsz' or filePath.suffix == '.xcz'

def isUncompressedGame(filePath):
	return filePath.suffix == '.nsp' or filePath.suffix == '.xci'

def isCompressedGame(filePath):
	return filePath.suffix == '.nsz' or filePath.suffix == '.xcz'

def isCompressedGameFile(filePath):
	return filePath.suffix == '.ncz'

def isNspNsz(filePath):
	return filePath.suffix == '.nsp' or filePath.suffix == '.nsz'

def isXciXcz(filePath):
	return filePath.suffix == '.xci' or filePath.suffix == '.xcz'

def changeExtension(filePath, newExtension):
	return str(filePath.parent.resolve().joinpath(filePath.stem + newExtension))

def getExtensionName(filePath):
	return str(Path(filePath).suffix[1:].upper())
