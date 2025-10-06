# install_startup.ps1
# This script creates a shortcut to the scanner in the Windows Startup folder,
# which makes the application launch automatically every time the user logs in.
# This only needs to be run once.

# --- Configuration ---
$ShortcutName = "Dhan Option Scanner.lnk"
$TargetScriptName = "start_scanner.bat"

# --- Script Logic ---
try {
    # Get the full path to the directory where this script is located
    $ScriptDir = $PSScriptRoot

    # Path to the batch file we want to run on startup
    $TargetFile = Join-Path -Path $ScriptDir -ChildPath $TargetScriptName

    # Check if the target batch file actually exists
    if (-not (Test-Path $TargetFile)) {
        Write-Error "Could not find the target script '$TargetScriptName' in the same directory."
        throw
    }

    # Get the path to the current user's Startup folder
    $StartupFolder = Join-Path -Path $env:APPDATA -ChildPath "Microsoft\Windows\Start Menu\Programs\Startup"

    # The full path for our new shortcut
    $ShortcutFile = Join-Path -Path $StartupFolder -ChildPath $ShortcutName

    # Create a Shell COM object, which is needed to create shortcuts
    $WshShell = New-Object -ComObject WScript.Shell

    # Create the shortcut object
    $Shortcut = $WshShell.CreateShortcut($ShortcutFile)

    # Set the properties for the shortcut
    $Shortcut.TargetPath = $TargetFile
    $Shortcut.WorkingDirectory = $ScriptDir # Important: ensures the script runs in the correct directory
    $Shortcut.Description = "Starts the Dhan Intraday Option Scanner."
    # You can also set an icon if you have one:
    # $Shortcut.IconLocation = "path\to\your\icon.ico"

    # Save the shortcut to the Startup folder
    $Shortcut.Save()

    Write-Host "==================================================================="
    Write-Host "[SUCCESS] Auto-start has been successfully configured."
    Write-Host "The Dhan Option Scanner will now launch automatically on login."
    Write-Host "There is no need to run this script again."
    Write-Host "==================================================================="

} catch {
    Write-Error "An error occurred during the setup: $_"
    Write-Error "Auto-start could not be configured."
}

# Pause the script so the user can read the final message
Read-Host "Press Enter to exit."