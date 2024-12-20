@ECHO OFF & CHCP 65001 1>NUL & COLOR 07
TITLE Get title keys

REM nsz.exe file path.
SET "nszFilePath=%~dp0nsz.exe"

REM Source directory path where to search for NSP/NSZ/XCI/XCZ files.
SET "SrcDirectoryPath=C:\Nintendo Switch dumps"

REM 'True' to enable recursive NSP/NSZ/XCI/XCZ file search on source directory, 'False' to disable it.
SET "EnableRecursiveSearch=False"

REM Additional nsz.exe parameters.
SET "AdditionalParameters=--alwaysParseCnmt"

:WELCOME_SCREEN
ECHO:╔══════════════════════════════════════════════════════╗
ECHO:║ TITLE   │ Extract title keys Script                  ║
ECHO:║_________│____________________________________________║
ECHO:║         │ Automates the extraction of title keys for ║
ECHO:║ PURPOSE │ Nintendo Switch NSP/NSZ/XCI/XCZ dumps.     ║
ECHO:║_________│____________________________________________║
ECHO:║ VERSION │ ElektroStudios - Ver. 1.2 'keep it simple' ║
ECHO:╚══════════════════════════════════════════════════════╝
ECHO+
ECHO:IMPORTANT: Before proceeding, open this script file in Notepad to adjust the following script settings as needed.
ECHO+
ECHO: ○ nsz.exe file path:
ECHO:   %nszFilePath%
ECHO+
ECHO: ○ Source directory path where to search for NSP/NSZ/XCI/XCZ files:
ECHO:   %SrcDirectoryPath%
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

:NSZ_WORK
REM FOR-loop logic.
IF /I "%EnableRecursiveSearch%" EQU "True" (
	SET "Params=/R "%SrcDirectoryPath%" %%# IN ("*.nsp" "*.xci")"
) ELSE (
	SET "Params=%%# IN ("%SrcDirectoryPath%\*.nsp" "%SrcDirectoryPath%\*.xci")"
)
FOR %Params% DO (
	TITLE nsz "%%~nx#"
	ECHO:Extracting title keys for "%%~f#"...
	ECHO+
	("%nszFilePath%" --info "%%~f#" --titlekeys %AdditionalParameters%) || (
		CALL :PRINT_ERROR_AND_EXIT nsz failed to parse file: "%%~f#"
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