from pathlib import Path
from traceback import format_exc
from hashlib import sha256
from nsz.nut import Print, aes128
from zstandard import ZstdDecompressor
from nsz.Fs import factory, Pfs0, Hfs0, Nsp, Xci
from nsz.PathTools import changeExtension, isCompressedGameFile, isNspNsz, isXciXcz
from nsz import Header, BlockDecompressorReader, FileExistingChecks
import os
import enlighten


class VerificationException(Exception):
    pass


def decompress(
    filePath, outputDir, fixPadding, statusReportInfo=None, pleaseNoPrint=None
):
    if isNspNsz(filePath):
        __decompressNsz(
            filePath,
            outputDir,
            fixPadding,
            True,
            False,
            False,
            None,
            statusReportInfo,
            pleaseNoPrint,
        )
    elif isXciXcz(filePath):
        __decompressXcz(
            filePath,
            outputDir,
            fixPadding,
            True,
            False,
            False,
            None,
            statusReportInfo,
            pleaseNoPrint,
        )
    elif isCompressedGameFile(filePath):
        filePathNca = changeExtension(filePath, ".nca")
        outPath = (
            filePathNca
            if outputDir is None
            else str(Path(outputDir).joinpath(Path(filePathNca).name))
        )
        Print.info(
            "Decompressing %s -> %s" % (filePath, outPath), pleaseNoPrint=pleaseNoPrint
        )
        inFile = None
        try:
            inFile = factory(filePath)
            inFile.open(str(filePath), "rb")
            with open(outPath, "wb") as outFile:
                written, hexHash = __decompressNcz(
                    inFile,
                    outFile,
                    statusReportInfo,
                    pleaseNoPrint,
                    None,
                    None,
                    None,
                    str(outPath),
                )
                fileNameHash = Path(filePath).stem.lower()
                if hexHash[:32] == fileNameHash:
                    Print.info(
                        "{0}".format(filePathNca),
                        "VERIFIED",
                        pleaseNoPrint=pleaseNoPrint,
                    )
                else:
                    Print.info(
                        "Filename starts with {0} but {1} was expected - hash verified failed!".format(
                            fileNameHash, hexHash[:32]
                        ),
                        "MISMATCH",
                        pleaseNoPrint=pleaseNoPrint,
                    )
                Print.progress("Complete", {"filePath": str(outPath)})
        except BaseException as ex:
            if not isinstance(ex, KeyboardInterrupt):
                Print.error(400, format_exc())
            if Path(outPath).is_file():
                Path(outPath).unlink()
        finally:
            if inFile is not None:
                inFile.close()
    else:
        raise NotImplementedError(
            "Can't decompress {0} as that file format isn't implemented!".format(
                filePath
            )
        )


def verify(
    filePath,
    fixPadding,
    raiseVerificationException,
    raisePfs0Exception,
    originalFilePath=None,
    statusReportInfo=None,
    pleaseNoPrint=None,
):
    if isNspNsz(filePath):
        __decompressNsz(
            filePath,
            None,
            fixPadding,
            False,
            raiseVerificationException,
            raisePfs0Exception,
            originalFilePath,
            statusReportInfo,
            pleaseNoPrint,
        )
    elif isXciXcz(filePath):
        __decompressXcz(
            filePath,
            None,
            fixPadding,
            False,
            raiseVerificationException,
            raisePfs0Exception,
            originalFilePath,
            statusReportInfo,
            pleaseNoPrint,
        )


def __decompressContainer(
    readContainer,
    writeContainer,
    fileHashes,
    write,
    raiseVerificationException,
    raisePfs0Exception,
    statusReportInfo,
    pleaseNoPrint,
    nczStepLabel=None,
):
    CHUNK_SZ = 0x100000
    if write:
        for nspf in readContainer:
            if not nspf._path.endswith(".ncz"):
                writeContainer.add(nspf._path, nspf.size, pleaseNoPrint)
            else:
                newFileName = Path(nspf._path).stem + ".nca"
                nca_size = __getDecompressedNczSize(nspf)
                writeContainer.add(newFileName, nca_size, pleaseNoPrint)
        writeContainer.updateHashHeader()

    barManager = None
    barState = [None, None]
    if (
        statusReportInfo is None
        and not Print.isMinimalOutput()
        and not Print.machineReadableOutput
    ):
        barManager = enlighten.get_manager()

    for nspf in readContainer:
        Print.info("{0}".format(nspf._path), "EXISTS", pleaseNoPrint=pleaseNoPrint)
        if not nspf._path.endswith(".ncz"):
            verifyFile = nspf._path.endswith(".nca") and not nspf._path.endswith(
                ".cnmt.nca"
            )
            hash = sha256()
            nspf.seek(0)
            while not nspf.eof():
                inputChunk = nspf.read(CHUNK_SZ)
                hash.update(inputChunk)
                if write:
                    writeContainer.get(nspf._path).write(inputChunk)
            if verifyFile:
                hashHexdigest = hash.hexdigest()
                if hasattr(nspf.f, "ticketless"):
                    # This ticket conditional was added to prevent the following exception from occurring when processing a ticketless dump file:
                    # NUT exception: Verification detected hash mismatch
                    Print.info(
                        "{0}".format(nspf._path),
                        "TICKETLESS",
                        pleaseNoPrint=pleaseNoPrint,
                    )
                else:
                    if hashHexdigest in fileHashes:
                        Print.info(
                            hashHexdigest, "NCA HASH", pleaseNoPrint=pleaseNoPrint
                        )
                        Print.info(
                            f"{nspf._path} {hashHexdigest}",
                            "VERIFIED",
                            pleaseNoPrint=pleaseNoPrint,
                        )
                    else:
                        Print.info(
                            hashHexdigest, "NCA HASH", pleaseNoPrint=pleaseNoPrint
                        )
                        Print.info(
                            f"{nspf._path} {hashHexdigest}",
                            "CORRUPTED",
                            pleaseNoPrint=pleaseNoPrint,
                        )
                        if raiseVerificationException:
                            raise VerificationException(
                                "Verification detected hash mismatch!"
                            )
            continue
        newFileName = Path(nspf._path).stem + ".nca"
        if write:
            written, hexHash = __decompressNcz(
                nspf,
                writeContainer.get(newFileName),
                statusReportInfo,
                pleaseNoPrint,
                nczStepLabel,
                barManager,
                barState,
                newFileName,
            )
        else:
            written, hexHash = __decompressNcz(
                nspf,
                None,
                statusReportInfo,
                pleaseNoPrint,
                nczStepLabel,
                barManager,
                barState,
                newFileName,
            )
        if hasattr(nspf.f, "ticketless"):
            # This ticket conditional was added to prevent the following exception from occurring when processing a ticketless dump file:
            # NUT exception: Verification detected hash mismatch
            Print.info(
                "{0}".format(nspf._path), "TICKETLESS", pleaseNoPrint=pleaseNoPrint
            )
        else:
            if hexHash in fileHashes:
                Print.info(hexHash, "NCA HASH", pleaseNoPrint=pleaseNoPrint)
                Print.info(
                    "{0}".format(nspf._path), "VERIFIED", pleaseNoPrint=pleaseNoPrint
                )
            else:
                Print.info(hexHash, "NCA HASH", pleaseNoPrint=pleaseNoPrint)
                Print.info(
                    "{0}".format(nspf._path), "CORRUPTED", pleaseNoPrint=pleaseNoPrint
                )
                if raiseVerificationException:
                    raise VerificationException("Verification detected hash mismatch")

    if barManager is not None:
        barManager.stop()


def __getDecompressedNczSize(nspf):
    INCOMPRESSIBLE_HEADER_SIZE = 0x4000
    nspf.seek(0)
    nspf.read(INCOMPRESSIBLE_HEADER_SIZE)
    magic = nspf.read(8)
    if not magic == b"NCZSECTN":
        raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
    sectionCount = nspf.readInt64()
    sections: list[Header.Section | Header.FakeSection] = [
        Header.Section(nspf) for _ in range(sectionCount)
    ]
    if sections[0].offset - INCOMPRESSIBLE_HEADER_SIZE > 0:
        fakeSection = Header.FakeSection(
            INCOMPRESSIBLE_HEADER_SIZE, sections[0].offset - INCOMPRESSIBLE_HEADER_SIZE
        )
        sections.insert(0, fakeSection)
    nca_size = INCOMPRESSIBLE_HEADER_SIZE
    for s in sections:
        nca_size += s.size
    # The first section can start inside the uncompressed NCA header (at 0xC00 in
    # small NCAs): those bytes are written once, as part of the header, so they
    # must not be counted twice
    if sections[0].offset < INCOMPRESSIBLE_HEADER_SIZE:
        nca_size -= INCOMPRESSIBLE_HEADER_SIZE - sections[0].offset
    return nca_size


def __decompressNcz(
    nspf,
    f,
    statusReportInfo,
    pleaseNoPrint,
    stepLabel=None,
    barManager=None,
    barState=None,
    outputName=None,
):
    INCOMPRESSIBLE_HEADER_SIZE = 0x4000
    nspf.seek(0)
    header = nspf.read(INCOMPRESSIBLE_HEADER_SIZE)
    if stepLabel is not None:
        currentStep = stepLabel
    else:
        currentStep = "Decompress" if f is not None else "Verifying"
    start = 0
    if f is not None:
        start = f.tell()
    magic = nspf.read(8)
    if not magic == b"NCZSECTN":
        raise ValueError("No NCZSECTN found! Is this really a .ncz file?")
    sectionCount = nspf.readInt64()
    sections: list[Header.Section | Header.FakeSection] = [
        Header.Section(nspf) for _ in range(sectionCount)
    ]
    if sections[0].offset - INCOMPRESSIBLE_HEADER_SIZE > 0:
        fakeSection = Header.FakeSection(
            INCOMPRESSIBLE_HEADER_SIZE, sections[0].offset - INCOMPRESSIBLE_HEADER_SIZE
        )
        sections.insert(0, fakeSection)
    nca_size = INCOMPRESSIBLE_HEADER_SIZE
    for s in sections:
        nca_size += s.size
    # The first section can start inside the uncompressed NCA header (at 0xC00 in
    # small NCAs): those bytes are written once, as part of the header, so they
    # must not be counted twice
    if sections[0].offset < INCOMPRESSIBLE_HEADER_SIZE:
        nca_size -= INCOMPRESSIBLE_HEADER_SIZE - sections[0].offset
    pos = nspf.tell()
    blockMagic = nspf.read(8)
    nspf.seek(pos)
    useBlockCompression = blockMagic == b"NCZBLOCK"
    blockDecompressorReader = None
    if useBlockCompression:
        Print.info(f"Using Block decompression for {nspf._path}", "NCZBLOCK")
        BlockHeader = Header.Block(nspf)
        blockDecompressorReader = BlockDecompressorReader.BlockDecompressorReader(
            nspf, BlockHeader
        )
    pos = nspf.tell()
    decompressor = None
    if not useBlockCompression:
        decompressor = ZstdDecompressor().stream_reader(nspf)
    hash = sha256()

    def reportProgress(processed):
        Print.progress(
            "Progress",
            {
                "sourceSize": nca_size,
                "processed": processed,
                "readSize": nspf.size,
                "read": nspf.tell(),
                "step": currentStep,
                "filePath": outputName,
            },
        )

    bar = None
    writtenBar = None
    ownBarManager = False
    if statusReportInfo is None:
        if not Print.isMinimalOutput() and not Print.machineReadableOutput:
            BAR_FMT = "{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
            if barManager is None:
                barManager = enlighten.get_manager()
                ownBarManager = True
            if barState is not None and barState[0] is not None:
                bar, writtenBar = barState
                bar.total = nspf.size // 1048576
                writtenBar.total = nca_size // 1048576
            else:
                bar = barManager.counter(
                    position=2,
                    total=nspf.size // 1048576,
                    desc="{0} Read   ".format(currentStep),
                    unit="MiB",
                    color="cyan",
                    bar_format=BAR_FMT,
                )
                writtenBar = barManager.counter(
                    position=1,
                    total=nca_size // 1048576,
                    desc="{0} Written".format(currentStep),
                    unit="MiB",
                    color="green",
                    bar_format=BAR_FMT,
                )
                if barState is not None:
                    barState[0] = bar
                    barState[1] = writtenBar
            bar.desc = "{0} Read   ".format(currentStep)
            writtenBar.desc = "{0} Written".format(currentStep)
            bar.count = 0
            writtenBar.count = 0
            bar.refresh()
            writtenBar.refresh()
        else:
            reportProgress(0)
    decompressedBytes = len(header)
    decompressedBytesOld = decompressedBytes
    if f is not None:
        f.write(header)
    statusReport = None
    id = None
    if statusReportInfo is not None:
        statusReport, id = statusReportInfo
        statusReport[id] = [len(header), 0, nca_size, currentStep]
    else:
        if not Print.isMinimalOutput() and not Print.machineReadableOutput:
            assert bar is not None and writtenBar is not None
            bar.count = nspf.tell() // 1048576
            writtenBar.count = decompressedBytes // 1048576
            bar.refresh()
            writtenBar.refresh()
        else:
            reportProgress(decompressedBytes)
    hash.update(header)

    firstSection = True
    for s in sections:
        i = s.offset
        useCrypto = s.cryptoType in (3, 4)
        crypto = None
        if useCrypto:
            assert isinstance(s, Header.Section)
            crypto = aes128.AESCTR(s.cryptoKey, s.cryptoCounter)
        end = s.offset + s.size
        if firstSection:
            firstSection = False
            uncompressedSize = INCOMPRESSIBLE_HEADER_SIZE - sections[0].offset
            if uncompressedSize > 0:
                i += uncompressedSize
        while i < end:
            if useCrypto:
                assert crypto is not None
                crypto.seek(i)
            chunkSz = 0x10000 if end - i > 0x10000 else end - i
            if useBlockCompression:
                assert blockDecompressorReader is not None
                inputChunk = blockDecompressorReader.read(chunkSz)
            else:
                assert decompressor is not None
                inputChunk = decompressor.read(chunkSz)
            if not len(inputChunk):
                break
            if useCrypto:
                assert crypto is not None
                inputChunk = crypto.encrypt(inputChunk)
            if f is not None:
                f.write(inputChunk)
            hash.update(inputChunk)
            lenInputChunk = len(inputChunk)
            i += lenInputChunk
            decompressedBytes += lenInputChunk
            if statusReportInfo is not None:
                assert statusReport is not None
                statusReport[id] = [
                    statusReport[id][0] + chunkSz,
                    statusReport[id][1],
                    nca_size,
                    currentStep,
                ]
            elif (
                decompressedBytes - decompressedBytesOld > 52428800
            ):  # Refresh every 50 MB
                decompressedBytesOld = decompressedBytes
                if not Print.isMinimalOutput() and not Print.machineReadableOutput:
                    assert bar is not None and writtenBar is not None
                    bar.count = nspf.tell() // 1048576
                    writtenBar.count = decompressedBytes // 1048576
                    bar.refresh()
                    writtenBar.refresh()
                else:
                    reportProgress(decompressedBytes)

    if statusReportInfo is None:
        if not Print.isMinimalOutput() and not Print.machineReadableOutput:
            assert bar is not None and writtenBar is not None
            bar.count = bar.total
            writtenBar.count = decompressedBytes // 1048576
            bar.refresh()
            writtenBar.refresh()
            if ownBarManager:
                assert barManager is not None
                barManager.stop()
        else:
            reportProgress(decompressedBytes)
    hexHash = hash.hexdigest()
    if f is not None:
        end = f.tell()
        written = end - start
        return (written, hexHash)
    return (0, hexHash)


def __decompressNsz(
    filePath,
    outputDir,
    fixPadding,
    write,
    raiseVerificationException,
    raisePfs0Exception,
    originalFilePath,
    statusReportInfo,
    pleaseNoPrint,
):
    container = Nsp.Nsp()
    container.open(str(filePath), "rb")
    fileHashes = FileExistingChecks.ExtractHashes(container)

    try:
        if write:
            filePathNsp = changeExtension(filePath, ".nsp")
            outPath = (
                filePathNsp
                if outputDir is None
                else str(Path(outputDir).joinpath(Path(filePathNsp).name))
            )
            Print.info(
                "Decompressing %s -> %s" % (filePath, outPath),
                pleaseNoPrint=pleaseNoPrint,
            )
            with Pfs0.Pfs0Stream(
                container.getPaddedHeaderSize()
                if fixPadding
                else container.getFirstFileOffset(),
                None if fixPadding else container.getStringTableSize(),
                outPath,
            ) as nsp:
                __decompressContainer(
                    container,
                    nsp,
                    fileHashes,
                    True,
                    raiseVerificationException,
                    raisePfs0Exception,
                    statusReportInfo,
                    pleaseNoPrint,
                    "Decompress",
                )
            if statusReportInfo is None:
                Print.progress("Complete", {"filePath": str(outPath)})
        else:
            with Pfs0.Pfs0VerifyStream(
                container.getPaddedHeaderSize()
                if fixPadding
                else container.getFirstFileOffset(),
                None if fixPadding else container.getStringTableSize(),
            ) as nsp:
                __decompressContainer(
                    container,
                    nsp,
                    fileHashes,
                    True,
                    raiseVerificationException,
                    raisePfs0Exception,
                    statusReportInfo,
                    pleaseNoPrint,
                    "Verifying",
                )
                Print.info(nsp.getHash(), "NSP SHA256")
                if originalFilePath is not None:
                    CHUNK_SZ = 0x100000
                    originalHash = sha256()
                    filesize = os.path.getsize(str(originalFilePath))
                    bar = None
                    if (
                        statusReportInfo is None
                        and not Print.isMinimalOutput()
                        and not Print.machineReadableOutput
                    ):
                        BAR_FMT = "{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
                        bar = enlighten.Counter(
                            total=filesize // CHUNK_SZ,
                            desc="Verifying",
                            unit="MiB",
                            color="yellow",
                            bar_format=BAR_FMT,
                        )
                    elif statusReportInfo is None:
                        Print.progress(
                            "Progress",
                            {
                                "sourceSize": filesize,
                                "processed": 0,
                                "step": "Verifying",
                            },
                        )
                    blockCount = 0
                    with open(str(originalFilePath), "rb") as f:
                        while True:
                            data = f.read(CHUNK_SZ)
                            blockCount += 1
                            if statusReportInfo is not None:
                                statusReport, id = statusReportInfo
                                statusReport[id] = [
                                    min(blockCount * CHUNK_SZ, filesize),
                                    0,
                                    filesize,
                                    "Verifying",
                                ]
                            else:
                                if (
                                    not Print.isMinimalOutput()
                                    and not Print.machineReadableOutput
                                ):
                                    assert bar is not None
                                    bar.count = blockCount
                                    bar.refresh()
                                else:
                                    Print.progress(
                                        "Progress",
                                        {
                                            "sourceSize": filesize,
                                            "processed": min(
                                                blockCount * CHUNK_SZ, filesize
                                            ),
                                            "step": "Verifying",
                                        },
                                    )
                            if not data:
                                break
                            originalHash.update(data)
                    originalHashHex = originalHash.hexdigest()
                    if (
                        statusReportInfo is None
                        and not Print.isMinimalOutput()
                        and not Print.machineReadableOutput
                    ):
                        assert bar is not None
                        bar.count = bar.total
                        bar.refresh()
                        bar.manager.stop()
                    elif statusReportInfo is None:
                        Print.progress("Complete", {"filePath": str(originalFilePath)})
                    Print.info(originalHashHex, "NSP SHA256")
                    if nsp.getHash() == originalHashHex:
                        Print.info("NSP SHA256", "VERIFIED")
                    else:
                        Print.info("NSP SHA256", "MISMATCH")
                        if raisePfs0Exception:
                            raise VerificationException(
                                "Verification detected NSP SHA256 hash mismatch!"
                            )
    except BaseException:
        raise
    finally:
        container.close()


def __decompressXcz(
    filePath,
    outputDir,
    fixPadding,
    write,
    raiseVerificationException,
    raisePfs0Exception,
    originalFilePath,
    statusReportInfo,
    pleaseNoPrint,
):
    container = Xci.Xci()
    container.open(str(filePath), "rb")

    if write:
        filePathXci = changeExtension(filePath, ".xci")
        outPath = (
            filePathXci
            if outputDir is None
            else str(Path(outputDir).joinpath(Path(filePathXci).name))
        )
        Print.info(
            "Decompressing %s -> %s" % (filePath, outPath), pleaseNoPrint=pleaseNoPrint
        )
        assert container.hfs0 is not None
        with Xci.XciStream(
            outPath, originalXciPath=filePath
        ) as xci:  # need filepath to copy XCI container settings
            assert xci.hfs0 is not None
            for partitionIn in container.hfs0:
                fileHashes = FileExistingChecks.ExtractHashes(partitionIn)
                hfsPartitionIn = xci.hfs0.add(partitionIn._path, 0x200, pleaseNoPrint)
                with Hfs0.Hfs0Stream(hfsPartitionIn, xci.f.tell()) as partitionOut:
                    __decompressContainer(
                        partitionIn,
                        partitionOut,
                        fileHashes,
                        write,
                        raiseVerificationException,
                        raisePfs0Exception,
                        statusReportInfo,
                        pleaseNoPrint,
                    )
                xci.hfs0.resize(partitionIn._path, partitionOut.actualSize)
        if statusReportInfo is None:
            Print.progress("Complete", {"filePath": str(outPath)})
    else:
        assert container.hfs0 is not None
        for partitionIn in container.hfs0:
            fileHashes = FileExistingChecks.ExtractHashes(partitionIn)
            __decompressContainer(
                partitionIn,
                None,
                fileHashes,
                write,
                raiseVerificationException,
                raisePfs0Exception,
                statusReportInfo,
                pleaseNoPrint,
            )

    container.close()
