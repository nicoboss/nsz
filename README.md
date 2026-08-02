[![Build Release Binaries](https://github.com/nicoboss/nsz/actions/workflows/build-release.yml/badge.svg)](https://github.com/nicoboss/nsz/actions/workflows/build-release.yml)

# NSZ

A compression/decompression script (with optional GUI) that compresses or decompresses Nintendo Switch dumps losslessly thanks to the [zstd](https://github.com/facebook/zstd) compression algorithm. The compressed file can be installed with supported NSW Homebrew Title Installers.

## Legal

- This project does **NOT** incorporate any copyrighted material such as cryptographic keys. All keys must be provided by the user.
- This project does **NOT** circumvent any technological protection measures. The NSZ file format purposely keeps all technological protection measures in place.
- This project shall only be used for legally purchased games or homebrew applications.
- This project is MIT licensed. Check [LICENSE](https://github.com/nicoboss/nsz/blob/master/LICENSE) for more information.

## Requirements

**You need to have a hactool compatible keys file in a suitable directory to use this tool**.

You must legally obtain your keys!

The keys file must be named either `prod.keys` or `keys.txt`. It must be located either in the directory in which you are running this software or:

| OS      | Location                                                        |
| ------- | --------------------------------------------------------------- |
| linux   | `$HOME/.switch/`, `$XDG_CONFIG_HOME/nsz/`, `$HOME/.config/nsz/` |
| macOS   | `$HOME/.switch/`                                                |
| windows | `%USERPROFILE%/.switch/`                                        |

You can also provide a custom keys path at runtime using the `--keys /path/to/prod.keys` parameter. This may be a direct path to the file or a directory containing `prod.keys` or `keys.txt`.

## Running this tool

There are several ways to run this tool. Choose from one of the methods below.

### Linux, Windows, and macOS binaries

You can find the binaries in the [release](https://github.com/nicoboss/nsz/releases/) page.

On most Linux systems you will need to right-click the file, open the properties, and choose to "Allow executing file as program".

Mac systems are much more strict about which software is allowed to be ran on the system. You must make the file executable from the terminal with `chmod +x nsz-cli-macos` or `chmod +x nsz-gui-macos`. After trying to run the program you will be stopped by security. Go to System Settings > Privacy & Security then scroll down and choose to allow running the program.

### Running from source

Requires [Python 3.6+](https://www.python.org/downloads).

This tool can be run from the [source code](https://github.com/nicoboss/nsz/archive/refs/heads/master.zip).

1. Run `pip3 install -r requirements.txt` to install the requirements for the CLI only, or `pip3 install -r requirements-gui.txt` to install the requirements for the CLI and GUI.
2. Run `python3 nsz.py` to start the program.

### PIP Package

Requires [Python 3.6+](https://www.python.org/downloads).

Use the following command to install the console-only version:

`pip3 install --upgrade nsz`

Use the following command to install the GUI version:

`pip3 install --upgrade nsz[gui]`

### Android

1. Install "Pydroid 3" and the "Pydroid repository plugin" from the Play Store
2. Open "Pydroid 3" and navigate to "Pip"
3. Enter "nsz" and unselect "use prebuild" then press install
4. Navigate to "Terminal" to use the "nsz" command
5. The first time it will tell you where to copy your prod.keys which you should do using the "cp" command
6. Use any command line arguments you want like "nsz -D file.nsz" to decompress your application

## Docker Container

NSZ is available as a Docker container with multi-architecture support for easy deployment and usage without needing to install Python.

The container provides:

- **Multi-architecture support**: linux/amd64, linux/arm64, linux/arm/v7, linux/ppc64le
- **Optimized size**: ~88MB Alpine-based image
- **Easy Nintendo Switch keys mounting**
- **Shell-like command usage**

For complete Docker setup, build instructions, and usage examples see [container/README.md](container/README.md).

Quick example:

```bash
# Build for local testing
make -C container build-single-arch

# Use with your Nintendo Switch keys
docker run --rm -v "$(pwd)":/data -v "$HOME/.switch/prod.keys":/root/.switch/prod.keys nsz-tool:latest application.nsp
```

## Usage

Comprehensive lists of command line parameters and usage examples are in the dedicated [usage documentation](docs/usage.md).

To view all possible flags and their descriptions check the [Usage](https://github.com/nicoboss/nsz#usage) section.

Automated bulk file operation examples are in [scripts](https://github.com/nicoboss/nsz/tree/master/scripts).

## File Format Details

Explanations of the file formats introduced by NSZ are found in the [formats documentation](docs/formats.md).

## Contributing

If you are interested in reporting/fixing issues and contributing directly to the code base, please see [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to get started.

## Mirrors

* [https://gitlab.nicobosshard.ch/nicoboss/nsz](https://gitlab.nicobosshard.ch/nicoboss/nsz).

The Swiss mirror will be the new home in case GitHub ever takes down this repository. Please bookmark it.

## References

NSZ pip package: <https://pypi.org/project/nsz/>

Forum thread: <https://gbatemp.net/threads/nsz-homebrew-compatible-nsp-xci-compressor-decompressor.550556/>

## License

Licensed under the [MIT](LICENSE) license.
