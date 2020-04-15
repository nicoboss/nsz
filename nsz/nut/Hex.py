from string import ascii_letters, digits, punctuation
from nsz.nut import Print

def bufferToHex(buffer, start, count):
    accumulator = ''
    for item in range(count):
        accumulator += '%02X' % buffer[start + item] + ' '
    return accumulator

def bufferToAscii(buffer, start, count):
    accumulator = ''
    for item in range(count):
        char = chr(buffer[start + item])
        if char in ascii_letters or \
           char in digits or \
           char in punctuation or \
           char == ' ':
            accumulator += char
        else:
            accumulator += '.'
    return accumulator

def dump(data, size = 16):
	bytesRead = len(data)
	index = 0
	hexFormat = '{:'+str(size*3)+'}'
	asciiFormat = '{:'+str(size)+'}'

	print()
	while index < bytesRead:
		
		hex = bufferToHex(data, index, size)
		ascii = bufferToAscii(data, index, size)

		print(hexFormat.format(hex), end='')
		print('|',asciiFormat.format(ascii),'|')
		
		index += size
		if bytesRead - index < size:
			size = bytesRead - index