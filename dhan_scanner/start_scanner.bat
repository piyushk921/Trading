@echo off
:: start_scanner.bat
:: This script activates the Python virtual environment and starts the scanner application.

:: Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

:: Check if the virtual environment exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at '%VENV_DIR%'.
    echo Please run the setup instructions in README.md to create it first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo [INFO] Starting the Dhan Option Scanner...
:: Use start "Scanner" to run the python process in a new window.
:: This allows this command prompt to close without terminating the scanner GUI.
start "Dhan Scanner" python "%SCRIPT_DIR%main.py"

echo [INFO] Scanner application has been launched in a new window.
echo This window can now be closed.

:: Deactivate is not strictly necessary as the script will exit,
:: but it's good practice.
call "%VENV_DIR%\Scripts\deactivate.bat"

exit /b 0