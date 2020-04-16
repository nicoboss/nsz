# NSZ
A compression/decompresson script (with optional GUI) that allows user to compress/decompress Nintendo Switch ROMs loselessly, thanks to [zstd](https://github.com/facebook/zstd) compression algorithm. The compressed file can be installed directly with supported NSW Homebrew Title Installers.

## Installation:
There are several ways to use the script. You can find details on installation for all below.\
\
**You need to have a hactool compatible keys file in a suitable directory to use the script**.\
The keys file must be located as `prod.keys` file in `%USERPROFILE%/.switch/`(Windows)/`$HOME/.switch/`(UNIX) or `keys.txt` in the working directory.\
\
It can be dumped with [Lockpick_RCM](https://github.com/shchmue/Lockpick_RCM/release).

### Windows Builds
You can also use the Windows binaries. They do not require any external libraries to be installed and can be run without installing anything. You can find the binaries in the [release](https://github.com/nicoboss/nsz/releases/) page.

**Methods listed below requires you to have Python 3.6+ and the pip package manager installed.**\
**Python 3.8 and later requires [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) if you are want to use the GUI.**

### PIP Package
Simplest way to install would be using the following command in a terminal or a command prompt.\
`pip3 install --upgrade nsz`

If you are interested in installing the GUI for the script, you can do so by running the following command.\
`pip3 install --upgrade nszgui`

### Running from source
The script can also be run by cloning the repo locally. You need to install the pre-requisite modules by running the following command.\
`pip3 install -r requirements.txt`

GUI is optional and requires extra modules to run with GUI. To install the modules required to run GUI, run the following command\
`pip3 install -r requirements-gui.txt`

## Usage
```
nsz.py --help
usage: nsz.py [-h] [-C] [-D] [-l LEVEL] [-B] [-S] [-s BS] [-V] [-p]
              [-t THREADS] [-m MULTI] [-o [OUTPUT]] [-w] [-r] [--rm-source]
              [-i] [--depth DEPTH] [-x] [--extractregex EXTRACTREGEX]
              [--titlekeys] [-c CREATE]
              [file [file ...]]

positional arguments:
  file

optional arguments:
  -h, --help            show this help message and exit
  -C                    Compress NSP/XCI
  -D                    Decompress NSZ/XCZ/NCZ
  -l LEVEL, --level LEVEL
                        Compression Level: Trade-off between compression speed
                        and compression ratio. Default: 18, Max: 22
  -B, --block           Use block compression option. This mode allows highly
                        multi-threaded compression/decompression with random
                        read access allowing compressed games to be played
                        without decompression in the future however this comes
                        with a slightly lower compression ratio cost. This is
                        the default option for XCZ.
  -S, --solid           Use solid compression option. Slightly higher
                        compression ratio but won't allow for random read
                        access. File compressed this way will never be
                        mountable (have to be installed or decompressed first
                        to run). This is the default option for NSZ.
  -s BS, --bs BS        Block Size for random read access 2^x while x between
                        14 and 32. Default: 20 => 1 MB
  -V, --verify          Verifies files after compression raising an unhandled
                        exception on hash mismatch and verify existing NSP and
                        NSZ files when given as parameter
  -p, --parseCnmt       Extract TitleId/Version from Cnmt if this information
                        cannot be obtained from the filename. Required for
                        skipping/overwriting existing files and --rm-old-
                        version to work properly if some not every file is
                        named properly. Supported filenames:
                        *TitleID*[vVersion]*
  -t THREADS, --threads THREADS
                        Number of threads to compress with. Numbers < 1
                        corresponds to the number of logical CPU cores for
                        block compression and 3 for solid compression
  -m MULTI, --multi MULTI
                        Executes multiple compression tasks in parallel. Take
                        a look at available RAM especially if compression
                        level is over 18.
  -o [OUTPUT], --output [OUTPUT]
                        Directory to save the output NSZ files
  -w, --overwrite       Continues even if there already is a file with the
                        same name or title id inside the output directory
  -r, --rm-old-version  Removes older versions if found
  --rm-source           Deletes source file/s after compressing/decompressing.
                        It's recommended to only use this in combination with
                        --verify
  -i, --info            Show info about title or file
  --depth DEPTH         Max depth for file info and extraction
  -x, --extract         Extract a NSP/XCI/NSZ/XCZ/NSPZ
  --extractregex EXTRACTREGEX
                        Regex specifying which files inside the container
                        should be extracted. Excample: "^.*\.(cert|tik)$"
  --titlekeys           Extracts titlekeys from your NSP/NSZ files and adds
                        missing keys to ./titlekeys.txt and JSON files inside
                        ./titledb/ (obtainable from
                        https://github.com/blawar/titledb). Titlekeys can be
                        used to unlock updates using NUT OG (OG fork
                        obtainable from https://github.com/plato79/nut). There
                        is currently no publicly known way of optioning NSX
                        files. To MitM: Apply disable_ca_verification &
                        disable_browser_ca_verification patches, use your
                        device's nx_tls_client_cert.pfx (Password: switch,
                        Install to OS and import for Fiddler or import into
                        Charles/OWASP ZAP). Use it for aauth-
                        lp1.ndas.srv.nintendo.net:443, dauth-
                        lp1.ndas.srv.nintendo.net:443 and
                        app-b01-lp1.npns.srv.nintendo.net:443. Try with your
                        WiiU first as there you won't get banned if you mess
                        up.
  -c CREATE, --create CREATE
                        create / pack a NSP
```

## Few Usage Examples
* To compress all files in a folder: `nsz -C /path/to/folder/with/roms/`
* To compress all files in a folder and verifying signature of compressed files: `nsz --verify -C /path/to/folder/with/roms/`
* To compress all files in a folder with 8 threads and outputting resulting files to a new directory: `nsz --threads 8 --output /path/to/out/dir/ -C /path/to/folder/with/roms/`
* To compress all files in a folder with level 22 compression level: `nsz --level 22 -C /path/to/folder/with/roms/`
* To decompress all files in a folder: `nsz -D /path/to/folder/with/roms/`

To view all the possible flags and a description on what each flag, check the [Usage](https://github.com/nicoboss/nsz#usage) section.

## File Format Details

### NSZ
NSZ files are not a real format, they are functionally identical to NSP files. Their sole purpose to alert the user that it contains compressed NCZ files. NCZ files can be mixed with NCA files in the same container.

NSC_Builder supports compressing NSP to NSZ, and decompressing NSZ to NSP. The sample scripts located here are just examples of how the format works.

NSC_Builder can be downloaded at https://github.com/julesontheroad/NSC_BUILDER

### XCZ
XCZ files are not a real format, they are functionally identical to XCI files. Their sole purpose to alert the user that it contains compressed NCZ files. NCZ files can be mixed with NCA files in the same container.

### NCZ
These are compressed NCA files. The NCA's are decrypted, and then compressed using zStandard. Only NCA's with a 0x4000 byte header are supported (CNMT nca's are not supported).

The first 0x4000 bytes of a NCZ file is exactly the same as the original NCA (and still encrypted).

At 0x4000, there is the variable sized NCZ Header. It contains a list of sections which tell the decompressor how to re-encrypt the NCA data after decompression. It can also contain an optional block compression header allowing random read access.

All of the information in the header can be derived from the original NCA + Ticket, however it is provided preparsed to make decompression as easy as possible for third parties.

Directly after the NCZ header, the zStandard stream begins and ends at EOF. The stream is decompressed to offset 0x4000. If block compression is used the stream is splatted into independent blocks and can be decompressed as shown in https://github.com/nicoboss/nsz/blob/master/nsz/BlockDecompressorReader.py

```python
class Section:
	def __init__(self, f):
		self.magic = f.read(8) # b'NCZSECTN'
		self.offset = f.readInt64()
		self.size = f.readInt64()
		self.cryptoType = f.readInt64()
		f.readInt64() # padding
		self.cryptoKey = f.read(16)
		self.cryptoCounter = f.read(16)

class Block:
	def __init__(self, f):
		self.magic = f.read(8) # b'NCZBLOCK'
		self.version = f.readInt8()
		self.type = f.readInt8()
		self.unused = f.readInt8()
		self.blockSizeExponent = f.readInt8()
		self.numberOfBlocks = f.readInt32()
		self.decompressedSize = f.readInt64()
		self.compressedBlockSizeList = []
		for i in range(self.numberOfBlocks):
			self.compressedBlockSizeList.append(f.readInt32())

nspf.seek(0x4000)
sectionCount = nspf.readInt64()
for i in range(sectionCount):
	sections.append(Section(nspf))

if blockCompression:
	BlockHeader = Block(nspf)
```

## References
NSZ pip package: https://pypi.org/project/nsz/  
Forum thread: https://gbatemp.net/threads/nsz-homebrew-compatible-nsp-xci-compressor-decompressor.550556/

## Credits
SciresM for his hardware crypto functions; the blazing install speeds (50 MB/sec +) achieved here would not be possible without this.

