#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from sys import argv
from nsz.nut import Keys, Print
from os import remove
from time import sleep
from nsz.Fs import Nsp, Xci, factory
from nsz.BlockCompressor import blockCompress
from nsz.SolidCompressor import solidCompress
from traceback import format_exc
from nsz.Decompressor import verify, decompress, VerificationException
from multiprocessing import cpu_count, freeze_support, Process, Manager
from nsz.FileExistingChecks import (
    CreateTargetDict,
    AllowedToWriteOutfile,
    delete_source_file,
)
from nsz.ParseArguments import ParseArguments
from nsz.PathTools import (
    changeExtension,
    expandFiles,
    getExtensionName,
    isCompressedGame,
    isCompressedGameFile,
    isGame,
    isUncompressedGame,
    isXciXcz,
)
from nsz.ExtractTitlekeys import extractTitlekeys
from nsz.undupe import undupe
from nsz.version import VERSION
import enlighten
import sys
import os
import warnings

warnings.filterwarnings(
    "ignore", message="unknown terminal capability", module="blessed.*"
)


class VerificationFailed:
    def __init__(self, exception, in_file):
        self.exception = exception
        self.in_file = in_file


if hasattr(sys, "getandroidapilevel"):
    from nsz.ThreadSafeCounterManager import Counter
else:
    from nsz.ThreadSafeCounterSharedMemory import Counter


def solidCompressTask(
    in_queue,
    statusReport,
    readyForWork,
    pleaseNoPrint,
    pleaseKillYourself,
    id,
    problemQueue,
    keysPath,
):
    if not Keys.keys_loaded:
        Keys.load_default(keysPath)
    while True:
        readyForWork.increment()
        item = in_queue.get()
        readyForWork.decrement()
        if pleaseKillYourself.value() > 0:
            break
        try:
            (
                filePath,
                compressionLevel,
                keep,
                fixPadding,
                useLongDistanceMode,
                outputDir,
                threadsToUse,
                verifyArg,
                quickVerify,
            ) = item
            outFile = solidCompress(
                filePath,
                compressionLevel,
                keep,
                fixPadding,
                useLongDistanceMode,
                outputDir,
                threadsToUse,
                statusReport,
                id,
                pleaseNoPrint,
            )
            if outFile is None:
                statusReport[id] = [0, 0, 1, "Failed"]
                problemQueue.put(
                    {
                        "filename": filePath,
                        "error": "Compression failed. Output file was not created.",
                    }
                )
                continue
            if verifyArg:
                Print.info("{0}".format(outFile), "VERIFY NSZ")
                try:
                    verify(
                        outFile,
                        fixPadding,
                        True,
                        keep,
                        None if quickVerify else filePath,
                        [statusReport, id],
                        pleaseNoPrint,
                    )
                except VerificationException as e:
                    Print.error(100, "[BAD VERIFY] {0}".format(outFile))
                    Print.error(101, "[DELETE NSZ] {0}".format(outFile))
                    remove(outFile)
                    problemQueue.put(VerificationFailed(exception=e, in_file=filePath))
                    continue
                except Keys.MissingKeyError:
                    raise
                except BaseException:
                    statusReport[id] = [0, 0, 1, "Failed"]
                    problemQueue.put(
                        {
                            "filename": filePath,
                            "error": format_exc(),
                        }
                    )
                    continue
        except KeyboardInterrupt:
            Print.info("Keyboard interrupt")
        except Keys.MissingKeyError as e:
            statusReport[id] = [0, 0, 1, "Failed"]
            problemQueue.put(
                {
                    "filename": locals().get("filePath", "<unknown>"),
                    "error": str(e),
                    "fatal": True,
                }
            )
            pleaseKillYourself.increment()
            break
        except BaseException as e:
            Print.info("NUT exception: {0}".format(str(e)))
            statusReport[id] = [0, 0, 1, "Failed"]
            problemQueue.put(
                {
                    "filename": locals().get("filePath", "<unknown>"),
                    "error": format_exc(),
                }
            )


def compress(filePath, outputDir, args, work, amountOfTaskQueued):
    compressionLevel = 18 if args.level is None else args.level

    if filePath.suffix == ".xci" and not args.solid or args.block:
        threadsToUseForBlockCompression = (
            args.threads if args.threads > 0 else cpu_count()
        )
        outFile = blockCompress(
            filePath,
            compressionLevel,
            args.keep,
            args.fix_padding,
            args.long,
            args.bs,
            outputDir,
            threadsToUseForBlockCompression,
        )
        assert outFile is not None
        if args.verify:
            Print.info("{0}".format(outFile), "VERIFY NSZ")
            try:
                verify(
                    outFile,
                    args.fix_padding,
                    True,
                    args.keep,
                    None if args.quick_verify else filePath,
                )
            except VerificationException:
                Print.error(100, "[BAD VERIFY] {0}".format(outFile))
                Print.error(101, "[DELETE NSZ] {0}".format(outFile))
                remove(outFile)
                raise
    else:
        threadsToUseForSolidCompression = args.threads if args.threads > 0 else 3
        work.put(
            [
                filePath,
                compressionLevel,
                args.keep,
                args.fix_padding,
                args.long,
                outputDir,
                threadsToUseForSolidCompression,
                args.verify,
                args.quick_verify,
            ]
        )
        amountOfTaskQueued.increment()


err = []

machineReadableOutput = False
minimalOutput = False


def configure_linux_gui_env():
    if not sys.platform.startswith("linux"):
        return

    # Ensure Kivy uses SDL2 and pick a sensible Linux video driver before
    # importing GUI modules. Users can override via environment variables.
    os.environ.setdefault("KIVY_WINDOW", "sdl2")
    requestedDriver = os.environ.get("NSZ_GUI_VIDEO_DRIVER")
    if requestedDriver:
        os.environ["SDL_VIDEODRIVER"] = requestedDriver
    elif "SDL_VIDEODRIVER" not in os.environ:
        if os.environ.get("WAYLAND_DISPLAY") and os.environ.get("DISPLAY"):
            # Packaged SDL2 commonly works more reliably via XWayland than native
            # Wayland in self-contained binaries.
            os.environ["SDL_VIDEODRIVER"] = "x11"
        elif os.environ.get("WAYLAND_DISPLAY"):
            os.environ["SDL_VIDEODRIVER"] = "wayland"
        elif os.environ.get("DISPLAY"):
            os.environ["SDL_VIDEODRIVER"] = "x11"


def configure_windows_gui_env():
    if not sys.platform.startswith("win"):
        return

    # Prefer ANGLE on Windows so GUI startup does not depend on legacy
    # OpenGL 1.1 driver compatibility in some VM/RDP/Wine contexts.
    os.environ.setdefault("KIVY_GL_BACKEND", "angle_sdl2")
    os.environ.setdefault("KIVY_GRAPHICS", "gles")


def _get_args():
    global machineReadableOutput
    global minimalOutput

    if len(argv) > 1:
        # There are command line arguments so assume that the user wants to interact through the command line.
        args = ParseArguments.parse()
        if args.machine_readable:
            machineReadableOutput = True
        if args.minimal_output:
            minimalOutput = True
        return args

    # There are no command line arguments. Open the GUI if it is available or print the help output.
    try:
        configure_windows_gui_env()
        configure_linux_gui_env()
        from nsz.gui.NSZ_GUI import launchGui
    except ImportError as e:
        Print.info("Unable to load NSZ_GUI: {0}".format(str(e)))
        Print.info("Proceeding in CLI mode.")
        ParseArguments.parse(args=["-h"])
        return None
    args = launchGui()
    if args is None:
        Print.info("Done!")
        return None
    return args


def _validate_output_mode(args):
    if args.quick_verify:
        args.verify = True

    if minimalOutput and machineReadableOutput:
        Print.error(
            107,
            "Error: --minimal-output and --machine-readable cannot be used together.",
        )
        return False

    if minimalOutput:
        Print.enableInfo = False

    return True


def _resolve_output_folder(args):
    """Returns (outFolder, ok). outFolder is None when not specified; ok is False on error."""
    if not args.output:
        return None, True

    argOutFolderToParse = args.output
    if not argOutFolderToParse.endswith("/") and not argOutFolderToParse.endswith("\\"):
        argOutFolderToParse += "/"
    if not Path(argOutFolderToParse).is_dir():
        Print.error(
            103,
            'Error: Output directory "{0}" does not exist!'.format(args.output),
        )
        return None, False
    return Path(argOutFolderToParse).resolve(), True


def _print_banner():
    leadingPadding = max(0, 13 - max(0, len(VERSION) - 3))
    Print.silly("")
    Print.silly("{0}NSZ v{1}   ,;:;;,".format(" " * leadingPadding, VERSION))
    Print.silly("                       ;;;;;")
    Print.silly("               .=',    ;:;;:,")
    Print.silly("              /_', \"=. ';:;:;")
    Print.silly("              @=:__,  \\,;:;:'")
    Print.silly("                _(\\.=  ;:;;'")
    Print.silly('               `"_(  _/="`')
    Print.silly("                `\"'")
    Print.silly("")


def _handle_extract(args, argOutFolder):
    for f_str in args.file:
        for filePath in expandFiles(Path(f_str)):
            filePath_str = str(filePath)
            outFolder = (
                argOutFolder.joinpath(filePath.stem)
                if argOutFolder
                else filePath.parent.absolute().joinpath(filePath.stem)
            )
            Print.info('Extracting "{0}" to {1}'.format(filePath_str, outFolder))
            container = factory(filePath)
            container.open(filePath_str, "rb")
            if isXciXcz(filePath):
                assert isinstance(container, Xci.Xci)
                assert container.hfs0 is not None
                for hfs0 in container.hfs0:
                    secureIn = hfs0
                    secureIn.unpack(outFolder.joinpath(hfs0._path), args.extractregex)
            else:
                assert isinstance(container, Nsp.Nsp)
                container.unpack(outFolder, args.extractregex)
            container.close()


def _handle_create(args):
    Print.info('Creating "{0}"'.format(args.create))
    nsp = Nsp.Nsp()
    nsp.path = args.create
    if not nsp.pack(args.file, args.fix_padding, args.overwrite):
        raise Exception


def _adjust_compression_verify_flags(args):
    if args.verify and not args.quick_verify and not args.keep:
        Print.info(
            "Warning: --verify requires --keep when used during compression or it will detect removed NDV0 fragments as errors. For compatibility reasons --quick-verify will be automatically used instead to match the command line argument behavior prior to NSZ v4.3.0."
        )
        args.quick_verify = True
    if args.verify and not args.quick_verify and args.fix_padding:
        Print.info(
            "Warning: --verify and --fix-padding are incompatible with each other. For compatibility reasons --quick-verify will be automatically used instead to match the command line argument behavior prior to NSZ v4.6.0."
        )
        args.quick_verify = True


def _queue_compression_jobs(
    args, argOutFolder, work, amountOfTaskQueued, targetDictNsz, targetDictXcz
):
    """Queues compression jobs and returns the list of source files to delete afterwards."""
    _adjust_compression_verify_flags(args)
    sourceFileToDelete = []
    for f_str in args.file:
        for filePath in expandFiles(Path(f_str)):
            if not isUncompressedGame(filePath):
                continue
            try:
                outFolder = argOutFolder if argOutFolder else filePath.parent.absolute()
                if filePath.suffix == ".nsp":
                    if outFolder not in targetDictNsz:
                        targetDictNsz[outFolder] = CreateTargetDict(
                            outFolder, args, ".nsz"
                        )
                    if not AllowedToWriteOutfile(
                        filePath, ".nsz", targetDictNsz[outFolder], args
                    ):
                        continue
                elif filePath.suffix == ".xci":
                    if outFolder not in targetDictXcz:
                        targetDictXcz[outFolder] = CreateTargetDict(
                            outFolder, args, ".xcz"
                        )
                    if not AllowedToWriteOutfile(
                        filePath, ".xcz", targetDictXcz[outFolder], args
                    ):
                        continue
                compress(filePath, outFolder, args, work, amountOfTaskQueued)
                if args.rm_source:
                    sourceFileToDelete.append(filePath)
            except KeyboardInterrupt:
                raise
            except Keys.MissingKeyError:
                raise
            except BaseException:
                Print.error(104, "Error while compressing file: %s" % filePath)
                err.append({"filename": filePath, "error": format_exc()})
                Print.exception()
    return sourceFileToDelete


def _start_compression_workers(
    parallelTasks,
    work,
    statusReport,
    readyForWork,
    pleaseNoPrint,
    pleaseKillYourself,
    problems,
    keysPath,
):
    for i in range(parallelTasks):
        statusReport.append([0, 0, 100, "Compressing"])
        p = Process(
            target=solidCompressTask,
            args=(
                work,
                statusReport,
                readyForWork,
                pleaseNoPrint,
                pleaseKillYourself,
                i,
                problems,
                keysPath,
            ),
        )
        p.start()


def _create_progress_bars(barManager, parallelTasks, BAR_FMT, WRITTEN_FMT):
    bars = []
    compressedSubBars = []
    assert barManager is not None
    totalBarLines = parallelTasks * 2
    for i in range(parallelTasks):
        bar = barManager.counter(
            position=totalBarLines - 2 * i,
            total=100,
            desc="Read",
            unit="MiB",
            color="cyan",
            bar_format=BAR_FMT,
        )
        compressedSubBar = barManager.counter(
            position=totalBarLines - 2 * i - 1,
            desc="Written",
            color="green",
            counter_format=WRITTEN_FMT,
        )
        bars.append(bar)
        compressedSubBars.append(compressedSubBar)
    return bars, compressedSubBars


def _print_compression_progress(parallelTasks, statusReport, bars, compressedSubBars):
    if minimalOutput:
        totalRead = 0
        totalSize = 0
        currentStep = "Compressing"
        for i in range(parallelTasks):
            compressedRead, _compressedWritten, total, step = statusReport[i]
            totalRead += compressedRead
            totalSize += total
            currentStep = step
        Print.progress(
            "Progress",
            {
                "sourceSize": totalSize,
                "processed": totalRead,
                "step": currentStep,
            },
        )
        return

    for i in range(parallelTasks):
        compressedRead, compressedWritten, total, currentStep = statusReport[i]
        if bars[i].total != total // 1048576:
            bars[i].total = total // 1048576
        bars[i].count = compressedRead // 1048576
        compressedSubBars[i].count = float(compressedWritten)
        bars[i].desc = "{0} Read   ".format(currentStep)
        compressedSubBars[i].desc = "{0} Written".format(currentStep)
        bars[i].refresh()
        compressedSubBars[i].refresh()


def _finish_compression_progress(
    parallelTasks, statusReport, bars, compressedSubBars, barManager
):
    if machineReadableOutput:
        return
    if minimalOutput:
        Print.progress("Complete", {"filePath": ""})
        return
    assert barManager is not None
    for i in range(parallelTasks):
        _compressedRead, compressedWritten, _total, _currentStep = statusReport[i]
        bars[i].count = bars[i].total
        compressedSubBars[i].count = float(compressedWritten)
        bars[i].refresh()
        compressedSubBars[i].refresh()
    barManager.stop()


def _run_compression(
    args,
    work,
    statusReport,
    readyForWork,
    pleaseNoPrint,
    pleaseKillYourself,
    problems,
    amountOfTaskQueued,
    barManager,
):
    BAR_FMT = "{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} {unit} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
    WRITTEN_FMT = "{desc}{desc_pad}{count:.2j}B [{elapsed}, {rate:.2j}B/s]"
    parallelTasks = min(args.multi, amountOfTaskQueued.value())
    if parallelTasks < 0:
        parallelTasks = 4

    # Start the compression tasks in parallel.
    _start_compression_workers(
        parallelTasks,
        work,
        statusReport,
        readyForWork,
        pleaseNoPrint,
        pleaseKillYourself,
        problems,
        args.keys,
    )

    bars, compressedSubBars = [], []
    if not machineReadableOutput and not minimalOutput:
        bars, compressedSubBars = _create_progress_bars(
            barManager, parallelTasks, BAR_FMT, WRITTEN_FMT
        )

    # Ensures that all threads are started and completed before being requested to quit
    while readyForWork.value() < parallelTasks:
        sleep(0.2)
        if pleaseNoPrint.value() > 0:
            continue
        if not problems.empty():
            problem = problems.get()
            if (
                isinstance(problem, dict)
                and problem.get("fatal")
                and "error" in problem
            ):
                raise Keys.MissingKeyError(problem["error"])
            err.append(problem)
        pleaseNoPrint.increment()

        # Show the progress bar only if the output is human readable.
        if not machineReadableOutput:
            _print_compression_progress(
                parallelTasks, statusReport, bars, compressedSubBars
            )

        pleaseNoPrint.decrement()
    pleaseKillYourself.increment()
    for i in range(readyForWork.value()):
        work.put(None)

    while readyForWork.value() > 0:
        sleep(0.02)

    _finish_compression_progress(
        parallelTasks, statusReport, bars, compressedSubBars, barManager
    )


def _delete_source_files(sourceFileToDelete, argOutFolder):
    for filePath in sourceFileToDelete:
        if argOutFolder:
            delete_source_file(filePath, argOutFolder)
        else:
            delete_source_file(filePath, filePath.parent.absolute())


def _handle_decompress(args, argOutFolder, targetDictNsz, targetDictXcz):
    for f_str in args.file:
        for filePath in expandFiles(Path(f_str)):
            if not isCompressedGame(filePath) and not isCompressedGameFile(filePath):
                continue
            try:
                outFolder = argOutFolder if argOutFolder else filePath.parent.absolute()
                if filePath.suffix == ".nsz":
                    if outFolder not in targetDictNsz:
                        targetDictNsz[outFolder] = CreateTargetDict(
                            outFolder, args, ".nsp"
                        )
                    if not AllowedToWriteOutfile(
                        filePath, ".nsp", targetDictNsz[outFolder], args
                    ):
                        continue
                elif filePath.suffix == ".xcz":
                    if outFolder not in targetDictXcz:
                        targetDictXcz[outFolder] = CreateTargetDict(
                            outFolder, args, ".xci"
                        )
                    if not AllowedToWriteOutfile(
                        filePath, ".xci", targetDictXcz[outFolder], args
                    ):
                        continue
                elif filePath.suffix == ".ncz":
                    outFile = Path(
                        changeExtension(outFolder.joinpath(filePath.name), ".nca")
                    )
                    if not args.overwrite and outFile.is_file():
                        Print.warning(
                            "A file with the same output name already exists."
                        )
                        continue
                decompress(filePath, outFolder, args.fix_padding)
                if args.rm_source:
                    delete_source_file(filePath, outFolder)
            except KeyboardInterrupt:
                raise
            except Keys.MissingKeyError:
                raise
            except BaseException:
                Print.error(105, "Error while decompressing file: {0}".format(filePath))
                err.append({"filename": filePath, "error": format_exc()})
                Print.exception()


def _handle_info(args):
    for f_str in args.file:
        for filePath in expandFiles(Path(f_str)):
            filePath_str = str(filePath)
            Print.info(filePath_str)
            f = factory(filePath)
            f.open(filePath_str, "rb")
            f.printInfo(args.depth + 1)
            f.close()


def _handle_verify(args):
    for f_str in args.file:
        for filePath in expandFiles(Path(f_str)):
            try:
                if isGame(filePath):
                    Print.info(
                        "[VERIFY {0}] {1}".format(
                            getExtensionName(filePath), filePath.name
                        )
                    )
                    verify(filePath, args.fix_padding, True, True)
            except KeyboardInterrupt:
                raise
            except Keys.MissingKeyError:
                raise
            except BaseException:
                Print.error(106, "Error while verifying file: {0}".format(filePath))
                err.append({"filename": filePath, "error": format_exc()})
                Print.exception()


def _report_errors():
    if machineReadableOutput:
        errors = []
        for e in err:
            if isinstance(e, VerificationFailed):
                errors.append({"filename": str(e.in_file), "message": str(e.exception)})
            else:
                errors.append({"filename": str(e["filename"]), "message": e["error"]})
        Print.summary(errors)
        return 1 if err else 0

    if not err:
        return 0
    Print.info(
        "\n\033[93m\033[1mSummary of errors which occurred while processing files:"
    )
    for e in err:
        if isinstance(e, VerificationFailed):
            Print.info(
                "\033[0mError while processing {0}: {1}".format(e.in_file, e.exception)
            )
        else:
            Print.info("\033[0mError while processing {0}".format(e["filename"]))
            Print.info(e["error"])
    return 1


def main():
    global err

    try:
        args = _get_args()
        if args is None:
            return

        if not _validate_output_mode(args):
            raise Exception("Invalid terminal output mode arguments.")

        argOutFolder, ok = _resolve_output_folder(args)
        if not ok:
            raise Exception("Unable to open output directory.")

        _print_banner()
        Print.startHeartbeat()

        barManager = (
            None
            if (machineReadableOutput or minimalOutput)
            else enlighten.get_manager()
        )
        poolManager = Manager()
        statusReport = poolManager.list()
        readyForWork = Counter(poolManager, 0)
        pleaseNoPrint = Counter(poolManager, 0)
        pleaseKillYourself = Counter(poolManager, 0)
        work = poolManager.Queue()
        problems = poolManager.Queue()
        amountOfTaskQueued = Counter(poolManager, 0)
        targetDictNsz = dict()
        targetDictXcz = dict()

        # Verify correct keys can be used
        keys_loaded = Keys.load_default(args.keys)
        if not keys_loaded:
            raise Exception("Could not load keys file.")

        if args.titlekeys:
            extractTitlekeys(args.file)

        if args.extract:
            _handle_extract(args, argOutFolder)

        if args.undupe or args.undupe_dryrun:
            undupe(args, argOutFolder)

        if args.create:
            _handle_create(args)

        if args.C:
            sourceFileToDelete = _queue_compression_jobs(
                args,
                argOutFolder,
                work,
                amountOfTaskQueued,
                targetDictNsz,
                targetDictXcz,
            )
            _run_compression(
                args,
                work,
                statusReport,
                readyForWork,
                pleaseNoPrint,
                pleaseKillYourself,
                problems,
                amountOfTaskQueued,
                barManager,
            )
            _delete_source_files(sourceFileToDelete, argOutFolder)

        if args.D:
            _handle_decompress(args, argOutFolder, targetDictNsz, targetDictXcz)

        if args.info:
            _handle_info(args)

        if args.verify and not args.C and not args.D:
            _handle_verify(args)

    except SystemExit:
        raise
    except KeyboardInterrupt:
        Print.info("Keyboard interrupt.")
    except Keys.MissingKeyError:
        # Print is handled in Keys.py
        sys.exit(1)
    except BaseException as e:
        Print.info("NUT exception.")
        # Stack trace is printed in nsz.py
        raise
    finally:
        Print.stopHeartbeat()

    exitCode = _report_errors()

    if len(argv) <= 1:
        input("Press Enter to exit...")
    sys.exit(exitCode)


if __name__ == "__main__":
    freeze_support()
    main()
