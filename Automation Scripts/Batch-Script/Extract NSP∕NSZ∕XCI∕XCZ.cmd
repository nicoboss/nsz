@ECHO OFF & CHCP 65001 1>NUL & COLOR 07
TITLE Extract NSP/NSZ/XCI/XCZ

:: nsz.exe file path.
SET "nszFilePath=%~dp0nsz.exe"

:: Source directory path where to search for NSP/NSZ/XCI/XCZ files.
SET "SrcDirectoryPath=C:\Nintendo Switch dumps"

:: Destination directory path where to extract NSP/NSZ/XCI/XCZ files.
SET "DstDirectoryPath=%SrcDirectoryPath%"

:: 'True' to enable recursive NSP/NSZ/XCI/XCZ file search on source directory, 'False' to disable it.
SET "EnableRecursiveSearch=False"

:: Additional NSZ parameters.
SET "AdditionalParameters=--alwaysParseCnmt --titlekeys --quick-verify"

:WELCOME_SCREEN
ECHO:╔══════════════════════════════════════════════════════════╗
ECHO:║ TITLE   │ Extract NSP/NSZ/XCI/XCZ Script                 ║
ECHO:║_________│________________________________________________║
ECHO:║         │ Automates the extraction of Nintendo Switch    ║
ECHO:║ PURPOSE │ NSP/NSZ/XCI/XCZ file content into directories. ║
ECHO:║_________│________________________________________________║
ECHO:║ VERSION │ ElektroStudios - Ver. 1.2 'keep it simple'     ║
ECHO:╚══════════════════════════════════════════════════════════╝
ECHO+
ECHO:IMPORTANT: Before proceeding, open this script file in Notepad to adjust the following script settings as needed.
ECHO+
ECHO: ○ nsz.exe file path:
ECHO:   %nszFilePath%
ECHO+
ECHO: ○ Source directory path where to search for NSP/NSZ/XCI/XCZ files:
ECHO:   %SrcDirectoryPath%
ECHO+
ECHO: ○ Destination directory path where to extract the content of NSP/NSZ/XCI/XCZ files:
ECHO:   %DstDirectoryPath%
ECHO+
ECHO: ○ Enable recursive NSP/NSZ/XCI/XCZ file search on source directory:
ECHO:   %EnableRecursiveSearch%
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
	SET "Params=/R "%SrcDirectoryPath%" %%# IN ("*.nsp" "*.nsz" "*.xci" "*.xcz")"
) ELSE (
	SET "Params=%%# IN ("%SrcDirectoryPath%\*.nsp" "%SrcDirectoryPath%\*.nsz" "%SrcDirectoryPath%\*.xci" "%SrcDirectoryPath%\*.xcz")"
)
FOR %Params% DO (
	TITLE nsz "%%~nx#"
	ECHO:Extracting "%%~f#"...
	ECHO+
	("%nszFilePath%" --extract "%%~f#" --output "%DstDirectoryPath%" %AdditionalParameters%) || (
		CALL :PRINT_ERROR_AND_EXIT "NSZ failed to extract file: "%%~f#""
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