from pathlib import Path

guiPath = Path(__file__).parent.resolve()

def getGuiPath(relativePath):
	return str(guiPath.joinpath(relativePath).resolve())
