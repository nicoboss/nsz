# Command line parameters

```
usage: nsz.py [-h] [-C] [-D] [-l LEVEL] [-L] [-B] [-S] [-s BS] [-V] [-Q] [-K] [-F] [-P] [-t THREADS]
              [-m MULTI] [-o [OUTPUT]] [-w] [-r] [--rm-source] [-i] [--depth DEPTH] [-x]
              [--extractregex EXTRACTREGEX] [--titlekeys] [--undupe] [--undupe-dryrun] [--undupe-rename]
              [--undupe-hardlink] [--undupe-prioritylist UNDUPE_PRIORITYLIST]
              [--undupe-whitelist UNDUPE_WHITELIST] [--undupe-blacklist UNDUPE_BLACKLIST]
              [--undupe-old-versions] [-c CREATE] [--machine-readable] [--minimal-output] [--keys KEYS]
              [file ...]

positional arguments:
  file

options:
  -h, --help            show this help message and exit
  -C                    Compress NSP/XCI
  -D                    Decompress NSZ/XCZ/NCZ
  -l, --level LEVEL     Compression Level: Trade-off between compression speed and compression ratio.
                        Default: 18, Max: 22
  -L, --long            Enables zStandard long distance mode for even better compression
  -B, --block           Use block compression option. This mode allows highly multi-threaded
                        compression/decompression with random read access allowing compressed games to be
                        played without decompression in the future however this comes with a slightly lower
                        compression ratio cost. This is the default option for XCZ.
  -S, --solid           Use solid compression option. Slightly higher compression ratio but won't allow for
                        random read access. File compressed this way will never be mountable (have to be
                        installed or decompressed first to run). This is the default option for NSZ.
  -s, --bs BS           Block Size for random read access 2^x while x between 14 and 32. Default: 20 => 1 MB
  -V, --verify          Verifies files after compression raising an unhandled exception on hash mismatch and
                        verify existing NSP and NSZ files when given as parameter. Requires --keep when used
                        during compression.
  -Q, --quick-verify    Same as --verify but skips the NSP SHA256 hash verification and only verifies NCA
                        hashes. Does not require --keep when used during compression.
  -K, --keep            Keep all useless files and partitions during compression to allow bit-identical
                        recreation
  -F, --fix-padding     Fixes PFS0 padding to match the nxdumptool/no-intro standard. Incompatible with
                        --verify so --quick-verify will be used instead.
  -P, --alwaysParseCnmt
                        Always extract TitleId/Version from Cnmt and never trust filenames
  -t, --threads THREADS
                        Number of threads to compress with. Numbers < 1 corresponds to the number of logical
                        CPU cores for block compression and 3 for solid compression
  -m, --multi MULTI     Executes multiple compression tasks in parallel. Take a look at available RAM
                        especially if compression level is over 18.
  -o, --output [OUTPUT]
                        Directory to save the output NSZ files
  -w, --overwrite       Continues even if there already is a file with the same name or title id inside the
                        output directory
  -r, --rm-old-version  Removes older versions if found
  --rm-source           Deletes source file/s after compressing/decompressing. It's recommended to only use
                        this in combination with --verify
  -i, --info            Show info about title or file
  --depth DEPTH         Max depth for file info and extraction
  -x, --extract         Extract a NSP/XCI/NSZ/XCZ/NSPZ
  --extractregex EXTRACTREGEX
                        Regex specifying which files inside the container should be extracted. Example:
                        "^.*\.(cert|tik)$"
  --titlekeys           Extracts titlekeys from your NSP/NSZ files and adds missing keys to ./titlekeys.txt
                        and JSON files inside ./titledb/ (obtainable from https://github.com/blawar/titledb).
  --undupe              Deleted all duplicates (games with same ID and Version). The Files folder will get
                        parsed in order so the later in the argument list the more likely the file is to be
                        deleted
  --undupe-dryrun       Shows what files would get deleted using --undupe
  --undupe-rename       Renames files to minimal standard: [TitleId][vVersion].nsz
  --undupe-hardlink     Hardlinks files to minimal standard: [TitleId][vVersion].nsz
  --undupe-prioritylist UNDUPE_PRIORITYLIST
                        Regex specifying which duplicate deletion should be prioritized before following the
                        normal deletion order. Example: "^.*\.(nsp|xci)$"
  --undupe-whitelist UNDUPE_WHITELIST
                        Regex specifying which duplicates should under no circumstances be deleted. Example:
                        "^.*\.(nsz|xcz)$"
  --undupe-blacklist UNDUPE_BLACKLIST
                        Regex specifying which files should always be deleted - even if they are not even a
                        duplicate! Be careful! Example: "^.*\.(nsp|xci)$"
  --undupe-old-versions
                        Removes every old version as long there is a newer one of the same titleID.
  -c, --create CREATE   Inverse of --extract. Repacks files/folders to an NSP. Example: --create out.nsp .\in
  --machine-readable    Restricts terminal output and reports in a way that is easier for a machine to read.
  --minimal-output      Print only minimal progress updates in the format "<percentage>% <current step>".
  --keys KEYS           Path to a hactool compatible keys file (or directory containing prod.keys/keys.txt).
```

# Usage Examples

## Compression

### Compress a single file

`nsz -C application.nsp`

### Compress all files in a folder

`nsz -C /path/to/folder/with/dumps/`

### Compress all files in a folder and verify their integrity

`nsz --verify -C /path/to/folder/with/dumps/`

### Compress all files in a folder and quickly verify their integrity

`nsz --quick-verify -C /path/to/folder/with/dumps/`

### Compress all files in a folder with a custom compression level

`nsz --level 22 -C /path/to/folder/with/dumps/`

### Compress all files in a folder using long distance mode for better compression

`nsz --long -C /path/to/folder/with/dumps/`

### Compress all files in a folder using block compression for random read access

`nsz --block -C /path/to/folder/with/dumps/`

### Compress all files in a folder using solid compression for maximum ratio

`nsz --solid -C /path/to/folder/with/dumps/`

### Compress all files in a folder with a custom block size for random read access

`nsz --block --bs 22 -C /path/to/folder/with/dumps/`

### Compress all files in a folder with 8 threads

`nsz --threads 8 -C /path/to/folder/with/dumps/`

### Compress all files in a folder running 2 compressions in parallel

`nsz --multi 2 -C /path/to/folder/with/dumps/`

### Compress all files in a folder and output to a new directory

`nsz --output /path/to/out/dir/ -C /path/to/folder/with/dumps/`

### Compress all files in a folder, overwriting any existing output files

`nsz --overwrite -C /path/to/folder/with/dumps/`

### Compress all files in a folder, removing older versions of the same title

`nsz --rm-old-version -C /path/to/folder/with/dumps/`

### Compress all files in a folder and delete the source files afterwards

`nsz --verify --rm-source -C /path/to/folder/with/dumps/`

### Compress all files in a folder, keeping useless files/partitions for bit-identical recreation

`nsz --keep -C /path/to/folder/with/dumps/`

### Compress all files in a folder, fixing PFS0 padding to the nxdumptool/no-intro standard

`nsz --fix-padding -C /path/to/folder/with/dumps/`

### Compress all files in a folder, always parsing TitleId/Version from Cnmt instead of trusting filenames

`nsz --alwaysParseCnmt -C /path/to/folder/with/dumps/`

## Decompression

### Decompress a single file

`nsz -D application.nsz`

### Decompress all files in a folder

`nsz -D /path/to/folder/with/dumps/`

### Decompress all files in a folder and output to a new directory

`nsz --output /path/to/out/dir/ -D /path/to/folder/with/dumps/`

### Decompress all files in a folder and delete the source files afterwards

`nsz --verify --rm-source -D /path/to/folder/with/dumps/`

## Verification

### Verify an existing NSP or NSZ file

`nsz --verify application.nsz`

### Quickly verify an existing NSP or NSZ file (NCA hashes only)

`nsz --quick-verify application.nsz`

## Extraction and Repacking

### Extract a NSP/XCI/NSZ/XCZ

`nsz --extract application.nsp`

### Extract a NSP/XCI/NSZ/XCZ to a custom depth

`nsz --extract --depth 1 application.nsp`

### Extract only files matching a regex from a NSP/XCI/NSZ/XCZ

`nsz --extract --extractregex "^.*\.(cert|tik)$" application.nsp`

### Repack a folder into a NSP

`nsz --create out.nsp .\in`

## Information

### Show info about a title or file

`nsz --info application.nsp`

### Show info about a title or file up to a custom depth

`nsz --info --depth 1 application.nsp`

## Title Keys

### Extract title keys from your NSP/NSZ files

`nsz --titlekeys /path/to/folder/with/dumps/`

## Deduplication

### Show which duplicate files would be deleted without deleting them

`nsz --undupe --undupe-dryrun /path/to/folder/with/dumps/`

### Delete duplicate files (same Title ID and Version), keeping the last one parsed

`nsz --undupe /path/to/folder/with/dumps/`

### Delete duplicate files, removing every old version once a newer one exists

`nsz --undupe --undupe-old-versions /path/to/folder/with/dumps/`

### Delete duplicate files, prioritizing NSP/XCI files for deletion first

`nsz --undupe --undupe-prioritylist "^.*\.(nsp|xci)$" /path/to/folder/with/dumps/`

### Delete duplicate files, never deleting NSZ/XCZ files

`nsz --undupe --undupe-whitelist "^.*\.(nsz|xcz)$" /path/to/folder/with/dumps/`

### Delete duplicate files, always deleting NSP/XCI files even if not a duplicate

`nsz --undupe --undupe-blacklist "^.*\.(nsp|xci)$" /path/to/folder/with/dumps/`

### Rename deduplicated files to the minimal `[TitleId][vVersion].nsz` standard

`nsz --undupe --undupe-rename /path/to/folder/with/dumps/`

### Hardlink deduplicated files to the minimal `[TitleId][vVersion].nsz` standard

`nsz --undupe --undupe-hardlink /path/to/folder/with/dumps/`

## Output Control

### Compress all files in a folder with machine-readable output

`nsz --machine-readable -C /path/to/folder/with/dumps/`

### Compress all files in a folder with minimal progress output

`nsz --minimal-output -C /path/to/folder/with/dumps/`

## Keys

### Compress all files in a folder using a custom keys file or directory

`nsz --keys /path/to/prod.keys -C /path/to/folder/with/dumps/`
