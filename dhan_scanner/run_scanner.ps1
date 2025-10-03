# run_scanner.ps1
# PowerShell script to activate the virtual environment and start the scanner.

# Get the directory where the script is located
$ScriptDir = $PSScriptRoot
$VenvDir = Join-Path -Path $ScriptDir -ChildPath "venv"
$VenvActivate = Join-Path -Path $VenvDir -ChildPath "Scripts\Activate.ps1"
$MainScriptPath = Join-Path -Path $ScriptDir -ChildPath "main.py"

# Check if the virtual environment activation script exists
if (-not (Test-Path $VenvActivate)) {
    Write-Error "Virtual environment not found at '$VenvDir'. Please run the setup instructions in README.md first."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if the main script exists
if (-not (Test-Path $MainScriptPath)) {
    Write-Error "Main script 'main.py' not found at '$MainScriptPath'."
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    Write-Host "[INFO] Activating virtual environment..."
    # The dot (.) operator runs the script in the current scope
    . $VenvActivate

    Write-Host "[INFO] Starting the Dhan Option Scanner..."
    # Start the python script as a separate process
    Start-Process python -ArgumentList $MainScriptPath -WindowStyle Normal

    Write-Host "[INFO] Scanner application has been launched in a new window."
    Write-Host "This PowerShell window can now be closed."

} catch {
    Write-Error "An error occurred while trying to start the scanner: $_"
} finally {
    # Deactivate the virtual environment if the function exists
    if (Get-Command -Name 'deactivate' -ErrorAction SilentlyContinue) {
        deactivate
    }
}

# The script will exit automatically, or you can uncomment the line below
# Read-Host "Press Enter to exit"