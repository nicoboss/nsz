import sys
from nsz.nut import Keys, Print
from time import sleep
from traceback import format_exc
from zstandard import ZstdCompressionParameters, ZstdCompressor
from nsz.SectionFs import isNcaPacked, sortedFs
from multiprocessing import Process, Manager
from nsz.Fs import Pfs0, Hfs0, Nca, Nsp, Type, Xci
import enlighten

if hasattr(sys, "getandroidapilevel"):
    from nsz.ThreadSafeCounterManager import Counter
else:
    from nsz.ThreadSafeCounterSharedMemory import Counter


def compressBlockTask(in_queue, out_list, readyForWork, pleaseKillYourself, blockSize):
    # On Windows, spawned worker processes don't inherit the parent's stdout/
    # stderr text encoding (PYTHONIOENCODING is set in the environment, but
    # each worker's own streams still default to the system's ANSI codepage).
    # Force UTF-8 here so this worker can't crash with a UnicodeEncodeError
    # the moment it needs to print something outside that codepage.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    while True:
        readyForWork.increment()
        item = in_queue.get()
        # readyForWork.decrement() # https://github.com/nicoboss/nsz/issues/80
        if pleaseKillYourself.value() > 0:
            break
        buffer, compressionLevel, useLongDistanceMode, chunkRelativeBlockID = item
        if buffer == 0:
            return
        if (
            compressionLevel == 0 and len(buffer) == blockSize
        ):  # https://github.com/nicoboss/nsz/issues/79
            out_list[chunkRelativeBlockID] = buffer
        else:
            params = ZstdCompressionParameters.from_level(
                compressionLevel, enable_ldm=useLongDistanceMode
            )
            compressed = ZstdCompressor(compression_params=params).compress(buffer)
            out_list[chunkRelativeBlockID] = (
                compressed if len(compressed) < len(buffer) else buffer
            )


def blockCompress(
    filePath,
    compressionLevel,
    keep,
    fixPadding,
    useLongDistanceMode,
    blockSizeExponent,
    outputDir,
    threads,
    statusReport=None,
    id=0,
):
    if filePath.suffix == ".nsp":
        return blockCompressNsp(
            filePath,
            compressionLevel,
            keep,
            fixPadding,
            useLongDistanceMode,
            blockSizeExponent,
            outputDir,
            threads,
            statusReport,
            id,
        )
    elif filePath.suffix == ".xci":
        return blockCompressXci(
            filePath,
            compressionLevel,
            keep,
            fixPadding,
            useLongDistanceMode,
            blockSizeExponent,
            outputDir,
            threads,
            statusReport,
            id,
        )


def blockCompressContainer(
    readContainer,
    writeContainer,
    compressionLevel,
    keep,
    useLongDistanceMode,
    blockSizeExponent,
    threads,
    statusReport=None,
    id=0,
):
    CHUNK_SZ = 0x100000
    INCOMPRESSIBLE_HEADER_SIZE = 0x4000

    machineReadableOutput = Print.machineReadableOutput
    minimalOutput = Print.isMinimalOutput()
    # When the caller polls a statusReport dict, skip the enlighten bars entirely
    useBars = statusReport is None and not machineReadableOutput and not minimalOutput

    if blockSizeExponent < 14 or blockSizeExponent > 32:
        raise ValueError("Block size must be between 14 and 32")
    blockSize = 2**blockSizeExponent
    manager = Manager()
    results = manager.list()
    readyForWork = Counter(manager, 0)
    pleaseKillYourself = Counter(manager, 0)
    TasksPerChunk = 209715200 // blockSize
    for i in range(TasksPerChunk):
        results.append(b"")
    pool = []
    work = manager.Queue(threads)

    for i in range(threads):
        p = Process(
            target=compressBlockTask,
            args=(work, results, readyForWork, pleaseKillYourself, blockSize),
        )
        p.start()
        pool.append(p)

    bar = None
    writtenBar = None
    barManager = None
    BAR_FMT = "{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
    WRITTEN_FMT = "{desc}{desc_pad}{count:.2j}B [{elapsed}, {rate:.2j}B/s]"
    WRITTEN_DESC = "Compressing Written"
    READ_DESC = "Compressing Read".ljust(len(WRITTEN_DESC))
    if useBars:
        barManager = enlighten.get_manager()

    for nspf in readContainer:
        if not keep:
            if isinstance(nspf, Nca.Nca) and nspf.header is not None:
                if nspf.header.contentType == Type.Content.DATA:
                    Print.info("Delta fragment {0}".format(nspf._path), "SKIPPED")
                    continue
        if (
            isinstance(nspf, Nca.Nca)
            and nspf.header is not None
            and nspf.size is not None
            and (
                nspf.header.contentType == Type.Content.PROGRAM
                or nspf.header.contentType == Type.Content.PUBLICDATA
            )
            and nspf.size > INCOMPRESSIBLE_HEADER_SIZE
        ):
            if isNcaPacked(nspf):
                assert nspf._path is not None
                offsetFirstSection = sortedFs(nspf)[0].offset
                newFileName = nspf._path[0:-1] + "z"

                def reportProgress(written, total):
                    Print.progress(
                        "Progress",
                        {
                            "sourceSize": total,
                            "processed": written,
                            "read": decompressedBytes,
                            "readSize": nspf.size,
                            "step": "Compressing",
                            "filePath": newFileName,
                        },
                    )

                f = writeContainer.add(newFileName, nspf.size)
                startPos = f.tell()
                nspf.seek(0)
                f.write(nspf.read(INCOMPRESSIBLE_HEADER_SIZE))
                sections = []

                for fs in sortedFs(nspf):
                    sections += fs.getEncryptionSections()

                if len(sections) == 0:
                    for p in pool:
                        # Process.terminate() might corrupt the data structure but we don't care
                        p.terminate()
                    raise Exception("NCA can't be decrypted. Outdated keys.txt?")
                header = b"NCZSECTN"
                header += len(sections).to_bytes(8, "little")
                i = 0

                for fs in sections:
                    i += 1
                    if not isinstance(fs.cryptoKey, (bytes, bytearray)):
                        raise ValueError(
                            "NCA cannot be compressed: missing title key for {0} (invalid section key).".format(
                                nspf._path
                            )
                        )
                    if len(fs.cryptoKey) != 0x10:
                        raise ValueError(
                            "NCA cannot be compressed: invalid section key length for {0}.".format(
                                nspf._path
                            )
                        )
                    if not isinstance(fs.cryptoCounter, (bytes, bytearray)):
                        raise ValueError(
                            "NCA cannot be compressed: invalid section counter for {0}.".format(
                                nspf._path
                            )
                        )
                    if len(fs.cryptoCounter) != 0x10:
                        raise ValueError(
                            "NCA cannot be compressed: invalid section counter length for {0}.".format(
                                nspf._path
                            )
                        )
                    header += fs.offset.to_bytes(8, "little")
                    header += fs.size.to_bytes(8, "little")
                    header += fs.cryptoType.to_bytes(8, "little")
                    header += b"\x00" * 8
                    header += fs.cryptoKey
                    header += fs.cryptoCounter

                f.write(header)
                blockID = 0
                chunkRelativeBlockID = 0
                startChunkBlockID = 0
                blocksHeaderFilePos = f.tell()
                bytesToCompress = nspf.size - INCOMPRESSIBLE_HEADER_SIZE
                blocksToCompress = bytesToCompress // blockSize + (
                    bytesToCompress % blockSize > 0
                )
                compressedblockSizeList = [0] * blocksToCompress
                header = b"NCZBLOCK"  # Magic
                header += b"\x02"  # Version
                header += b"\x01"  # Type
                header += b"\x00"  # Unused
                header += blockSizeExponent.to_bytes(
                    1, "little"
                )  # blockSizeExponent in bits: 2^x
                header += blocksToCompress.to_bytes(4, "little")  # Amount of Blocks
                header += bytesToCompress.to_bytes(8, "little")  # Decompressed Size
                header += b"\x00" * (blocksToCompress * 4)
                f.write(header)
                decompressedBytes = INCOMPRESSIBLE_HEADER_SIZE
                compressedBytes = f.tell()
                if statusReport is not None:
                    statusReport[id] = [decompressedBytes, compressedBytes, nspf.size, "Compressing"]
                reportProgress(compressedBytes, nspf.size)

                if useBars:
                    assert barManager is not None
                    if bar is None:
                        bar = barManager.counter(
                            position=2,
                            total=nspf.size // 1048576,
                            desc=READ_DESC,
                            unit="MiB",
                            color="cyan",
                            bar_format=BAR_FMT,
                        )
                        writtenBar = barManager.counter(
                            position=1,
                            desc=WRITTEN_DESC,
                            color="green",
                            counter_format=WRITTEN_FMT,
                        )
                    else:
                        assert writtenBar is not None
                        bar.total = nspf.size // 1048576
                    bar.count = 0
                    writtenBar.count = 0.0
                    bar.refresh()
                    writtenBar.refresh()

                partitions = []
                if offsetFirstSection - INCOMPRESSIBLE_HEADER_SIZE > 0:
                    partitions.append(
                        nspf.partition(
                            offset=INCOMPRESSIBLE_HEADER_SIZE,
                            size=offsetFirstSection - INCOMPRESSIBLE_HEADER_SIZE,
                            cryptoType=Type.Crypto.CTR.NONE,
                            autoOpen=True,
                        )
                    )
                for section in sections:
                    # Print.info('offset: %x\t\tsize: %x\t\ttype: %d\t\tiv%s' % (section.offset, section.size, section.cryptoType, str(hx(section.cryptoCounter))))
                    partitions.append(
                        nspf.partition(
                            offset=section.offset,
                            size=section.size,
                            cryptoType=section.cryptoType,
                            cryptoKey=section.cryptoKey,
                            cryptoCounter=bytearray(section.cryptoCounter),
                            autoOpen=True,
                        )
                    )
                if INCOMPRESSIBLE_HEADER_SIZE - offsetFirstSection > 0:
                    partitions[0].seek(INCOMPRESSIBLE_HEADER_SIZE - offsetFirstSection)

                partNr = 0
                decompressedBytesOld = nspf.tell() // 1048576

                if useBars:
                    assert bar is not None and writtenBar is not None
                    bar.count = nspf.tell() // 1048576
                    writtenBar.count = float(f.tell())
                    bar.refresh()
                    writtenBar.refresh()

                while True:
                    buffer = partitions[partNr].read(blockSize)
                    while len(buffer) < blockSize and partNr < len(partitions) - 1:
                        partitions[partNr].close()
                        partitions[partNr] = None
                        partNr += 1
                        buffer += partitions[partNr].read(blockSize - len(buffer))
                    if chunkRelativeBlockID >= TasksPerChunk or len(buffer) == 0:
                        while readyForWork.value() < threads:
                            sleep(0.02)

                        for i in range(
                            min(TasksPerChunk, blocksToCompress - startChunkBlockID)
                        ):
                            lenResult = len(results[i])
                            compressedBytes += lenResult
                            compressedblockSizeList[startChunkBlockID + i] = lenResult
                            f.write(results[i])
                            results[i] = b""

                        if len(buffer) == 0:
                            break
                        chunkRelativeBlockID = 0
                        startChunkBlockID = blockID
                    work.put(
                        [
                            buffer,
                            compressionLevel,
                            useLongDistanceMode,
                            chunkRelativeBlockID,
                        ]
                    )
                    readyForWork.decrement()
                    blockID += 1
                    chunkRelativeBlockID += 1
                    decompressedBytes += len(buffer)
                    if (
                        decompressedBytes - decompressedBytesOld > 10485760
                    ):  # Refresh every 10 MB
                        decompressedBytesOld = decompressedBytes

                        if statusReport is not None:
                            statusReport[id] = [decompressedBytes, compressedBytes, nspf.size, "Compressing"]
                        if useBars:
                            assert bar is not None and writtenBar is not None
                            bar.count = decompressedBytes // 1048576
                            writtenBar.count = float(compressedBytes)
                            bar.refresh()
                            writtenBar.refresh()
                        else:
                            reportProgress(compressedBytes, nspf.size)

                    sys.stdout.flush()
                partitions[partNr].close()
                partitions[partNr] = None
                endPos = f.tell()
                written = endPos - startPos

                if statusReport is not None:
                    statusReport[id] = [decompressedBytes, written, nspf.size, "Compressing"]
                if useBars:
                    assert bar is not None and writtenBar is not None
                    bar.count = bar.total
                    writtenBar.count = float(written)
                    bar.refresh()
                    writtenBar.refresh()
                else:
                    reportProgress(written, written)

                f.seek(blocksHeaderFilePos + 24)
                header = b""

                for compressedblockSize in compressedblockSizeList:
                    header += compressedblockSize.to_bytes(4, "little")

                f.write(header)
                f.seek(endPos)  # Seek to end of file.
                Print.info(
                    "compressed %d%% %d -> %d  - %s"
                    % (
                        int(written * 100 / nspf.size),
                        decompressedBytes,
                        written,
                        nspf._path,
                    )
                )
                writeContainer.resize(newFileName, written)
                continue
            else:
                Print.info("Skipping not packed {0}".format(nspf._path))
        f = writeContainer.add(nspf._path, nspf.size)
        nspf.seek(0)
        while not nspf.eof():
            buffer = nspf.read(CHUNK_SZ)
            f.write(buffer)

    # Ensures that all threads are started and completed before being requested to quit
    while readyForWork.value() < threads:
        sleep(0.02)
    pleaseKillYourself.increment()

    for i in range(readyForWork.value()):
        work.put(None)
        readyForWork.decrement()

    while readyForWork.value() > 0:
        sleep(0.02)

    if barManager is not None:
        barManager.stop()


def blockCompressNsp(
    filePath,
    compressionLevel,
    keep,
    fixPadding,
    useLongDistanceMode,
    blockSizeExponent,
    outputDir,
    threads,
    statusReport=None,
    id=0,
):
    filePath = filePath.resolve()
    container = Nsp.Nsp()
    container.open(str(filePath), "rb")
    nszPath = outputDir.joinpath(filePath.stem + ".nsz")

    Print.info(
        f"Block compressing (level {compressionLevel}{' ldm' if useLongDistanceMode else ''}) {filePath} -> {nszPath}"
    )

    try:
        with Pfs0.Pfs0Stream(
            container.getPaddedHeaderSize()
            if fixPadding
            else container.getFirstFileOffset(),
            None if fixPadding else container.getStringTableSize(),
            str(nszPath),
        ) as nsp:
            blockCompressContainer(
                container,
                nsp,
                compressionLevel,
                keep,
                useLongDistanceMode,
                blockSizeExponent,
                threads,
                statusReport,
                id,
            )

        Print.progress("Complete", {"filePath": str(nszPath)})
        sys.stdout.flush()
    except BaseException as ex:
        if isinstance(ex, Keys.MissingKeyError):
            raise
        if not isinstance(ex, KeyboardInterrupt):
            Print.error(200, format_exc())
        if nszPath.is_file():
            nszPath.unlink()

    container.close()
    return nszPath


def align0x200(n):
    return 0x200 - n % 0x200


def blockCompressXci(
    filePath,
    compressionLevel,
    keep,
    fixPadding,
    useLongDistanceMode,
    blockSizeExponent,
    outputDir,
    threads,
    statusReport=None,
    id=0,
):
    filePath = filePath.resolve()
    container = Xci.Xci()
    container.open(str(filePath), "rb")
    xczPath = outputDir.joinpath(filePath.stem + ".xcz")

    Print.info(
        f"Block compressing (level {compressionLevel}{' ldm' if useLongDistanceMode else ''}) {filePath} -> {xczPath}"
    )

    try:
        # need filepath to copy XCI container settings
        assert container.hfs0 is not None
        with Xci.XciStream(str(xczPath), originalXciPath=filePath) as xci:
            assert xci.hfs0 is not None
            for partitionIn in container.hfs0:
                xci.hfs0.written = False
                hfsPartitionOut = xci.hfs0.add(partitionIn._path, 0)
                with Hfs0.Hfs0Stream(hfsPartitionOut, xci.f) as partitionOut:
                    if keep or partitionIn._path == "secure":
                        blockCompressContainer(
                            partitionIn,
                            partitionOut,
                            compressionLevel,
                            keep,
                            useLongDistanceMode,
                            blockSizeExponent,
                            threads,
                            statusReport,
                            id,
                        )
                    alignedSize = partitionOut.actualSize + align0x200(
                        partitionOut.actualSize
                    )
                    xci.hfs0.resize(partitionIn._path, alignedSize)
                    Print.info(f"{partitionIn._path} to {hex(alignedSize)}", "RESIZE")
                    xci.hfs0.addpos += alignedSize

        Print.progress("Complete", {"filePath": str(xczPath)})
        sys.stdout.flush()
    except BaseException as ex:
        if isinstance(ex, Keys.MissingKeyError):
            raise
        if not isinstance(ex, KeyboardInterrupt):
            Print.error(201, format_exc())
        if xczPath.is_file():
            xczPath.unlink()

    container.close()
    return xczPath
