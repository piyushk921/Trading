# daily_check.ps1
# A PowerShell script to perform a daily health check of the scanner setup.

# Get the directory where the script is located
$ScriptDir = $PSScriptRoot
$LogFile = Join-Path -Path $ScriptDir -ChildPath "logs\scanner.log"
$VenvDir = Join-Path -Path $ScriptDir -ChildPath "venv"
$DotEnvFile = Join-Path -Path $ScriptDir -ChildPath ".env"

# --- Health Check Functions ---

Function Check-EnvironmentVariables {
    Write-Host "`n--- 1. Checking Environment Variables ---"
    $RequiredVars = @(
        "DHAN_CLIENT_ID",
        "DHAN_ACCESS_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    )

    $AllVarsSet = $true

    # Check for .env file first
    if (Test-Path $DotEnvFile) {
        Write-Host "[INFO] Found .env file. Checking contents..."
        $envContent = Get-Content $DotEnvFile
        foreach ($var in $RequiredVars) {
            if ($envContent -match "^$var=") {
                Write-Host "[OK] '$var' is present in .env file."
            } else {
                Write-Host "[FAIL] '$var' is MISSING from .env file."
                $AllVarsSet = $false
            }
        }
    } else {
        Write-Host "[INFO] .env file not found. Checking system/user environment variables..."
        foreach ($var in $RequiredVars) {
            if (Test-Path "Env:$var") {
                Write-Host "[OK] '$var' is set in the environment."
            } else {
                Write-Host "[FAIL] '$var' is NOT set in the environment."
                $AllVarsSet = $false
            }
        }
    }

    if (-not $AllVarsSet) {
        Write-Warning "One or more required secrets are missing. The scanner will fail to start."
    } else {
        Write-Host "[SUCCESS] All required secrets appear to be configured."
    }
}

Function Check-VenvHealth {
    Write-Host "`n--- 2. Checking Virtual Environment ---"
    $PythonExe = Join-Path -Path $VenvDir -ChildPath "Scripts\python.exe"
    if (Test-Path $PythonExe) {
        Write-Host "[SUCCESS] Virtual environment looks healthy ('$PythonExe' found)."
    } else {
        Write-Warning "Virtual environment is missing or corrupted. Python executable not found at '$PythonExe'."
        Write-Warning "Please run the setup instructions in the README.md file."
    }
}

Function Check-LastRunStatus {
    Write-Host "`n--- 3. Checking Last Scanner Run Status (from logs) ---"
    if (-not (Test-Path $LogFile)) {
        Write-Warning "Log file not found at '$LogFile'. Cannot determine last run status."
        return
    }

    # Get the last 20 lines from the log file
    $LastLines = Get-Content $LogFile -Tail 20
    $LastScanLine = $LastLines | Where-Object { $_ -match "Scan cycle finished" } | Select-Object -Last 1

    if ($LastScanLine) {
        # Extract timestamp from the line (e.g., "2024-10-03 10:05:30")
        $TimestampStr = ($LastScanLine -split ' \| ')[0]
        try {
            $LastScanTimestamp = [datetime]::ParseExact($TimestampStr, "yyyy-MM-dd HH:mm:ss", $null)
            $TimeSinceLastScan = (Get-Date) - $LastScanTimestamp

            Write-Host "[INFO] Last successful scan cycle finished at: $LastScanTimestamp"
            Write-Host "[INFO] Time since last scan: $($TimeSinceLastScan.Days) days, $($TimeSinceLastScan.Hours) hours, $($TimeSinceLastScan.Minutes) minutes."

            if ($TimeSinceLastScan.TotalHours -gt 4) {
                 Write-Warning "It has been over 4 hours since the last successful scan cycle. Please check if the scanner is running correctly."
            } else {
                 Write-Host "[SUCCESS] Scanner appears to have run recently."
            }
        } catch {
             Write-Warning "Could not parse timestamp from log line: $LastScanLine"
        }
    } else {
        Write-Warning "No 'Scan cycle finished' message found in the last 20 log entries. The scanner may not be running or may be encountering errors."
    }
}

# --- Execute Checks ---
Write-Host "========================================"
Write-Host " Dhan Scanner Daily Health Check"
Write-Host "========================================"

Check-EnvironmentVariables
Check-VenvHealth
Check-LastRunStatus

Write-Host "`n--- Health Check Complete ---"
Read-Host "Press Enter to exit"