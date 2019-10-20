## NSZ
NSZ files are not a real format, they are functionally identical to NSP files.  Their sole purpose to alert the user that it contains compressed NCZ files.  NCZ files can be mixed with NCA files in the same container.

NSC_Builder supports compressing NSP to NSZ, and decompressing NSZ to NSP.  The sample scripts located here are just examples of how the format works.

NSC_Builder can be downloaded at https://github.com/julesontheroad/NSC_BUILDER

## XCZ
XCZ files are not a real format, they are functionally identical to XCI files.  Their sole purpose to alert the user that it contains compressed NCZ files.  NCZ files can be mixed with NCA files in the same container.

## NCZ

These are compressed NCA files.  The NCA's are decrypted, and then compressed using zstandard.  Only NCA's with a 0x4000 byte header are supported (CNMT nca's are not supported).

The first 0x4000 bytes of a NCZ file is exactly the same as the original NCA (its still encrypted as well).

At 0x4000, there will be a variable sized NCZ Header structure.  This header contains a list of sections which tell the decompressor how to re-encrypt the NCA data after decompression.

All of the information in the header can be derived from the original NCA + Ticket, however it is provided preparsed to make decompression as easy as possible for third parties.

Directly after the NCZ header, the zstandard stream begins and ends at EOF.  The stream is decompressed to offset 0x4000.

```cpp
class NczHeader
{
public:
	class Section
	{
	public:
		u64 offset;
		u64 size;
		u8 cryptoType;
		u8 padding1[7];
		u64 padding2;
		integer<128> cryptoKey;
		integer<128> cryptoCounter;
	} PACKED;

	const bool isValid()
	{
		return m_magic == MAGIC && m_sectionCount < 0xFFFF;
	}

	const u64 size() const
	{
		return sizeof(m_magic) + sizeof(m_sectionCount) + sizeof(Section) * m_sectionCount;
	}

	const Section& section(u64 i) const
	{
		return m_sections[i];
	}

protected:
	u64 m_magic;
	u64 m_sectionCount;
	Section m_sections[1];

	static const u64 MAGIC = 0x4E544345535A434E;
} PACKED;
```


## Compressor script

Requires hactool compatible keys.txt to be present with nsz.py.  Only currently works with base games, updates, and DLC.

example usage:
nsz.py --level 18 -C title1.nsp title2.nsp title3.nsp

will generate title1.nsz title2.nsz title3.nsz

## Python requirements

py -3 -m pip install -r requirements.txt

## Usage
```
nsz.py --help
usage: nsz.py [-h] [-i INFO] [--depth DEPTH] [-V] [-x EXTRACT [EXTRACT ...]]
              [-c CREATE] [-C] [-D] [-l LEVEL] [-B] [-s BS] [-t THREADS]
              [-o OUTPUT] [-w]
              [file [file ...]]

positional arguments:
  file

optional arguments:
  -h, --help            show this help message and exit
  -i INFO, --info INFO  show info about title or file
  --depth DEPTH         max depth for file info and extraction
  -V, --verify          Verify NSP and NSZ files
  -x EXTRACT [EXTRACT ...], --extract EXTRACT [EXTRACT ...]
                        extract / unpack a NSP
  -c CREATE, --create CREATE
                        create / pack a NSP
  -C                    Compress NSP
  -D                    Decompress NSZ
  -l LEVEL, --level LEVEL
                        Compression Level
  -B, --block           Uses highly multithreaded block compression with
                        random read access allowing compressed games to be
                        played without decompression in the future however
                        this comes with a low compression ratio cost. Current
                        title installers do not support this yet.
  -s BS, --bs BS        Block Size for random read access 2^x while x between
                        14 and 32. Default is 20 => 1 MB. Current title
                        installers do not support this yet.
  -t THREADS, --threads THREADS
                        Number of threads to compress with. Usless without
                        enabeling block compression using -B. Negative
                        corresponds to the number of logical CPU cores.
  -o OUTPUT, --output OUTPUT
                        Directory to save the output NSZ files
  -w, --overwrite       Overwrite file if it exists in the output folder
```

## Credits

SciresM for his hardware crypto functions; the blazing install speeds (50 MB/sec +) achieved here would not be possible without this.

Nicoboss for the original awesome idea.  https://github.com/nicoboss/nsZip/
