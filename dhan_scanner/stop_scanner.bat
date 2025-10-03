@echo off
:: stop_scanner.bat
:: This script finds and terminates the Dhan Option Scanner process.

echo [INFO] Attempting to find and stop the Dhan Option Scanner process...

:: Find the process by the window title "Dhan Scanner" that was set in start_scanner.bat
:: The `taskkill` command will be used to terminate it.
:: The /FI flag filters tasks, and /IM is for image name. However, since we used `start "Title"`,
:: the python.exe process might not be uniquely identifiable.
:: A more reliable way is to find the python process running our main.py.

:: This command finds python processes and checks their command line for "main.py".
for /f "tokens=2" %%i in ('wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid /value') do (
    set "PID=%%i"
)

if defined PID (
    echo [SUCCESS] Found scanner process with PID: %PID%.
    taskkill /PID %PID% /F
    echo [SUCCESS] Scanner process terminated.
) else (
    echo [WARNING] Scanner process not found. It might already be closed.
)

pause
exit /b 0