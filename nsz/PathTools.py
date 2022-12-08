from pathlib import Path
from os import listdir

def expandFiles(path):
	files = []
	path = path.resolve()

	if path.is_file():
		files.append(path)
	else:
		for f_str in listdir(path):
			f = Path(f_str)
			f = path.joinpath(f)
			files.append(f)
	return files
	

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

def targetExtension(filePath):
	if filePath.suffix == '.nsp': newExtension = '.nsz'
	if filePath.suffix == '.xci': newExtension = '.xcz'
	if filePath.suffix == '.nca': newExtension = '.ncz'
	if filePath.suffix == '.nsz': newExtension = '.nsp'
	if filePath.suffix == '.xcz': newExtension = '.xci'
	if filePath.suffix == '.ncz': newExtension = '.nca'
	return str(filePath.parent.resolve().joinpath(filePath.stem + newExtension))

def getExtensionName(filePath):
	return str(Path(filePath).suffix[1:].upper())

