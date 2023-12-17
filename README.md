# NSZ
A compression/decompresson script (with optional GUI) that allows user to compress/decompress Nintendo Switch ROMs loselessly, thanks to [zstd](https://github.com/facebook/zstd) compression algorithm. The compressed file can be installed directly with supported NSW Homebrew Title Installers.

## Legal
- This project does NOT incorporate any copyrighted material such as cryptographic keys. All keys must be provided by the user.
- This project does NOT circumvent any technological protection measures. The NSZ file format purposely keeps all technological protection measures in place by not decrypting the most crucial parts.
- This project shall only be used for legally purchased games.
- This project is MIT licensed. Check [LICENSE](https://github.com/nicoboss/nsz/blob/master/LICENSE) for more information.

## Installation:
There are several ways the install the script. You can find details on installation for all of them below.\
\
**You need to have a hactool compatible keys file in a suitable directory to use the script**.\
The keys file must be located as `prod.keys` file in `%USERPROFILE%/.switch/`(Windows)/`$HOME/.switch/`(UNIX) or `keys.txt` in the working directory.\
\
It can be dumped using Lockpick_RCM.

### Windows Builds
You can also use the Windows binaries. They do not require any external libraries to be installed and can be run without installing anything. You can find the binaries in the [release](https://github.com/nicoboss/nsz/releases/) page.

**Methods listed below requires you to have Python 3.6+ and pip3 installed.**

### PIP Package
Use the following command to install the console-only version:\
`pip3 install --upgrade nsz`

Use the following command to install the GUI version:\
`pip3 install --upgrade nsz[gui]`

### Android
1. Install "Pydroid 3" and the "Pydroid repository plugin" from the Play Store
2. Open "Pydroid 3" and navigate to "Pip"
3. Enter "nsz" and unselect "use prebuild" then press install
4. Navigate to "Terminal" to use the "nsz" command
5. The first time it will tell you where to copy your prod.keys which you should do using the "cp" command
6. Use any command line arguments you want like "nsz -D file.nsz" to decompress your game

### Running from source
The tool can also be run by cloning the repository, installing the requirements and then executing nsz using `python3 nsz.py`

Use the following command to install the console-only versions requirements:\
`pip3 install -r requirements.txt`

Use the following command to install the GUI versions requirements:\
`pip3 install -r requirements-gui.txt`

## Usage
```
nsz.py --help
usage: nsz.py [-h] [-C] [-D] [-l LEVEL] [-L] [-B] [-S] [-s BS] [-V] [-Q] [-K]
              [-F] [-p] [-P] [-t THREADS] [-m MULTI] [-o [OUTPUT]] [-w] [-r]
              [--rm-source] [-i] [--depth DEPTH] [-x]
              [--extractregex EXTRACTREGEX] [--titlekeys] [--undupe]
              [--undupe-dryrun] [--undupe-rename] [--undupe-hardlink]
              [--undupe-prioritylist UNDUPE_PRIORITYLIST]
              [--undupe-whitelist UNDUPE_WHITELIST]
              [--undupe-blacklist UNDUPE_BLACKLIST] [--undupe-old-versions]
              [-c CREATE]
              [file ...]

positional arguments:
  file

options:
  -h, --help            show this help message and exit
  -C                    Compress NSP/XCI
  -D                    Decompress NSZ/XCZ/NCZ
  -l LEVEL, --level LEVEL
                        Compression Level: Trade-off between compression speed
                        and compression ratio. Default: 18, Max: 22
  -L, --long            Enables zStandard long distance mode for even better
                        compression
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
                        NSZ files when given as parameter. Requires --keep
                        when used during compression.
  -Q, --quick-verify    Same as --verify but skips the NSP SHA256 hash
                        verification and only verifies NCA hashes. Does not
                        require --keep when used during compression.
  -K, --keep            Keep all useless files and partitions during
                        compression to allow bit-identical recreation
  -F, --fix-padding     Fixes PFS0 padding to match the nxdumptool/no-intro
                        standard. Incompatible with --verify so --quick-verify
                        will be used instead.
  -p, --parseCnmt       Extract TitleId/Version from Cnmt if this information
                        cannot be obtained from the filename. Required for
                        skipping/overwriting existing files and --rm-old-
                        version to work properly if some not every file is
                        named properly. Supported filenames:
                        *TitleID*[vVersion]*
  -P, --alwaysParseCnmt
                        Always extract TitleId/Version from Cnmt and never
                        trust filenames
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
                        should be extracted. Example: "^.*\.(cert|tik)$"
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
  --undupe              Deleted all duplicates (games with same ID and
                        Version). The Files folder will get parsed in order so
                        the later in the argument list the more likely the
                        file is to be deleted
  --undupe-dryrun       Shows what files would get deleted using --undupe
  --undupe-rename       Renames files to minimal standard:
                        [TitleId][vVersion].nsz
  --undupe-hardlink     Hardlinks files to minimal standard:
                        [TitleId][vVersion].nsz
  --undupe-prioritylist UNDUPE_PRIORITYLIST
                        Regex specifying which dublicate deletion should be
                        prioritized before following the normal deletion
                        order. Example: "^.*\.(nsp|xci)$"
  --undupe-whitelist UNDUPE_WHITELIST
                        Regex specifying which dublicates should under no
                        circumstances be deleted. Example: "^.*\.(nsz|xcz)$"
  --undupe-blacklist UNDUPE_BLACKLIST
                        Regex specifying which files should always be deleted
                        - even if they are not even a dublicate! Be careful!
                        Example: "^.*\.(nsp|xci)$"
  --undupe-old-versions
                        Removes every old version as long there is a newer one
                        of the same titleID.
  -c CREATE, --create CREATE
                        Inverse of --extract. Repacks files/folders to an NSP.
                        Example: --create out.nsp .\in
```

## Few Usage Examples
* To compress all files in a folder: `nsz -C /path/to/folder/with/roms/`
* To compress all files in a folder and verifying integrity of compressed files: `nsz --verify -C /path/to/folder/with/roms/`
* To compress all files in a folder with 8 threads and outputting resulting files to a new directory: `nsz --threads 8 --output /path/to/out/dir/ -C /path/to/folder/with/roms/`
* To compress all files in a folder with level 22 compression level: `nsz --level 22 -C /path/to/folder/with/roms/`
* To decompress all files in a folder: `nsz -D /path/to/folder/with/roms/`

To view all the possible flags and a description on what each flag, check the [Usage](https://github.com/nicoboss/nsz#usage) section.

## File Format Details

### NSZ
NSZ files are functionally identical to NSP files. Their sole purpose to alert the user that it contains compressed NCZ files. NCZ files can be mixed with NCA files in the same container.

As an alternative to this tool NSC_Builder also supports compressing NSP to NSZ, and decompressing NSZ to NSP. NSC_Builder can be downloaded at https://github.com/julesontheroad/NSC_BUILDER

### XCZ
XCZ files are functionally identical to XCI files. Their sole purpose to alert the user that it contains compressed NCZ files. NCZ files can be mixed with NCA files in the same container.

### NCZ
These are compressed NCA files. The NCA's are decrypted, and then compressed using zStandard.

The first 0x4000 bytes of an NCZ file is exactly the same as the original NCA (and still encrypted). This applies even if the first section doesn't start at 0x4000.

At 0x4000, there is the variable sized NCZ Header. It contains a list of sections which tell the decompressor how to re-encrypt the NCA data after decompression. It can also contain an optional block compression header allowing random read access.

All of the information in the header can be derived from the original NCA + Ticket, however it is provided pre-parsed to make decompression as easy as possible for third parties.

Directly after the NCZ header, the zStandard stream begins and ends at EOF. The stream is decompressed to offset 0x4000. If block compression is used the stream is splitted into independent blocks and can be decompressed as shown in https://github.com/nicoboss/nsz/blob/master/nsz/BlockDecompressorReader.py. CompressedBlockSizeList[blockID] must not exceed decompressedBlockSize. If smaller the block must be decompressed. If equal the block is stored in plain text.

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

Thanks to our contributors: nicoboss, blawar, plato79, eXhumer, Taorni, anthonyu, teknoraver, KWottrich, gabest11, siddhartha77, alucryd, seiya-git, drizzt, 16BitWonder, 2weak2live, thatch, maki-chan, pR0Ps
