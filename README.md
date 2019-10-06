## NSZ
NSZ files are not a real format, they are functionally identical to NSP files.  Their sole purpose to alert the user that it contains compressed NCZ files.  NCZ files can be mixed with NCA files in the same container.

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

Requires hactool compatible keys.txt to be present with nsz.py.

example usage:
nsz.py -C title.nsp --level 17

will generate title.nsz
