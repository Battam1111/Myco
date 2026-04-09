@echo off
REM Myco PyPI Upload Script
REM ======================
REM Usage: Double-click this file, or run from project root.
REM Requires: PyPI API token in %USERPROFILE%\.pypirc (see PYPI_SETUP.md)

set SCRIPTS_DIR=%USERPROFILE%\AppData\Roaming\Python\Python313\Scripts
set DIST_DIR=%~dp0..\dist

echo.
echo [Myco] Uploading to PyPI...
echo.

if not exist "%DIST_DIR%\myco-0.9.0-py3-none-any.whl" (
    echo [ERROR] dist/ not found. Run: python -m build
    exit /b 1
)

"%SCRIPTS_DIR%\twine.exe" upload "%DIST_DIR%\*"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Published! https://pypi.org/project/myco/
) else (
    echo.
    echo [FAIL] Upload failed. Check your API token in %%USERPROFILE%%\.pypirc
)
