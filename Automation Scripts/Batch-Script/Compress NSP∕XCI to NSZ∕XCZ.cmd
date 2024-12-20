@ECHO OFF & CHCP 65001 1>NUL & COLOR 07
TITLE Compress NSP/XCI to NSZ/XCZ

REM nsz.exe file path.
SET "nszFilePath=%~dp0nsz.exe"

REM Source directory path where to search for NSP/XCI files.
SET "SrcDirectoryPath=C:\Nintendo Switch dumps"

REM Destination directory path where to save generated NSZ/XCZ files.
SET "DstDirectoryPath=%SrcDirectoryPath%"

REM 'True' to enable recursive NSP/XCI file search on source directory, 'False' to disable it.
SET "EnableRecursiveSearch=False"

REM nsz.exe compression level (maximum value is 22, default is 18).
SET /A "CompressionLevel=22"

REM Additional nsz.exe parameters.
SET "AdditionalParameters=--long --solid --alwaysParseCnmt --undupe-rename --titlekeys --quick-verify"

:WELCOME_SCREEN
ECHO:╔═══════════════════════════════════════════════════════════╗
ECHO:║ TITLE   │ Compress NSP/XCI to NSZ/XCZ Script              ║
ECHO:║_________│_________________________________________________║
ECHO:║         │ Automates the compression of Nintendo Switch    ║
ECHO:║ PURPOSE │ NSP/XCI dumps into NSZ/XCZ format respectively. ║
ECHO:║_________│_________________________________________________║
ECHO:║ VERSION │ ElektroStudios - Ver. 1.2 'keep it simple'      ║
ECHO:╚═══════════════════════════════════════════════════════════╝
ECHO+
ECHO:IMPORTANT: Before proceeding, open this script file in Notepad to adjust the following script settings as needed.
ECHO+
ECHO: ○ nsz.exe full path:
ECHO:   %nszFilePath%
ECHO+
ECHO: ○ Source directory path where to search for NSP/XCI files:
ECHO:   %SrcDirectoryPath%
ECHO+
ECHO: ○ Destination directory path where to save NSZ/XCZ files:
ECHO:   %DstDirectoryPath%
ECHO+
ECHO: ○ Enable recursive NSP/XCI file search on source directory:
ECHO:   %EnableRecursiveSearch%
ECHO+
ECHO: ○ nsz.exe compression level (max. value is 22):
ECHO:   %CompressionLevel%
ECHO+
ECHO: ○ Additional nsz.exe parameters:
ECHO:   %AdditionalParameters%
ECHO+
PAUSE
CLS

:PRIMARY_CHECKS
REM Ensure nsz.exe file exists.
IF NOT EXIST " %nszFilePath%" (
	CALL :PRINT_ERROR_AND_EXIT nsz.exe file does not exists: "%nszFilePath%"
)
REM Ensure the source directory exists.
IF NOT EXIST "%SrcDirectoryPath%" (
	CALL :PRINT_ERROR_AND_EXIT Source directory does not exists: "%SrcDirectoryPath%"
)
REM Ensure the output directory can be created.
MKDIR "%DstDirectoryPath%" 1>NUL 2>&1 || (
	IF NOT EXIST "%DstDirectoryPath%" (
		CALL :PRINT_ERROR_AND_EXIT Output directory can't be created: "%DstDirectoryPath%"
	)
)

:NSZ_WORK
REM FOR-loop logic.
IF /I "%EnableRecursiveSearch%" EQU "True" (
	SET "Params=/R "%SrcDirectoryPath%" %%# IN ("*.nsp" "*.xci")"
) ELSE (
	SET "Params=%%# IN ("%SrcDirectoryPath%\*.nsp" "%SrcDirectoryPath%\*.xci")"
)
FOR %Params% DO (
	TITLE nsz "%%~nx#"
	ECHO:Compressing "%%~f#"...
	ECHO+
	("%nszFilePath%" -C "%%~f#" --output "%DstDirectoryPath%" --level %CompressionLevel% %AdditionalParameters%) || (
		CALL :PRINT_ERROR_AND_EXIT "NSZ failed to compress file: "%%~f#""
	)
)

:GOODBYE_SCREEN
COLOR 0A
ECHO+
ECHO:Operation Completed!
ECHO+
PAUSE & EXIT 0

:PRINT_ERROR_AND_EXIT
COLOR 0C
ECHO+
ECHO:ERROR OCCURRED: %*
ECHO+
PAUSE & EXIT 1