def sortedFs(nca):
	fs = [i for i in nca.sections]
	fs.sort(key=lambda x: x.offset)
	return fs

def isNcaPacked(nca, ncaHeaderSize):
	fs = sortedFs(nca)
	if len(fs) == 0:
		return True
	next = ncaHeaderSize

	for i in range(len(fs)):
		if fs[i].offset != next:
			return False
		next = fs[i].offset + fs[i].size

	if next != nca.size:
		return False
	return True