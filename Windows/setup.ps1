#Requires -RunAsAdministrator

$forwarder = "splunkforwarder-10.0.1-c486717c322b-windows-x64.msi"
$url = "https://download.splunk.com/products/universalforwarder/releases/10.0.1/windows/$forwarder"
$splunkPath = "C:\Program Files\SplunkUniversalForwarder\bin\splunk.exe"

# --- 1. Download & Install Splunk Universal Forwarder ---
try {
    Write-Host "Downloading $forwarder..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $url -OutFile $forwarder -ErrorAction Stop
    Write-Host "Download Complete" -ForegroundColor Green
}
catch {
    Write-Error "Download failed: $_"
    exit
}

try {
    Write-Host "Launching installer..." -ForegroundColor Cyan
    # Added AGREETOLICENSE=Yes to prevent error 1603, plus logging (/l*v install.log)
    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$forwarder`" AGREETOLICENSE=Yes /qn /norestart /l*v install.log" -Wait -PassThru -ErrorAction Stop
    
    if ($process.ExitCode -ne 0) {
        throw "Installer exited with code $($process.ExitCode). Check install.log for details."
    }
    Write-Host "Installer finished successfully" -ForegroundColor Green
}
catch {
    Write-Error "Failed to launch installer: $_"
    exit
}

# --- 2. Prompt for User Inputs ---
Write-Host "`n--- Splunk Configuration ---" -ForegroundColor Yellow
$server = Read-Host "What is the Server IP?"
$port = Read-Host "What is the Server Receiving Port?"
$indexer = "$server`:$port"

$username = Read-Host "Splunk Username"
$securePassword = Read-Host "Enter Splunk Password" -AsSecureString
# Convert secure string back to plain text for the splunk CLI auth flag
$password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword))
$login = "$username`:$password"

$hostname = Read-Host "Enter a hostname for this client"

# --- 3. Functions ---
function Invoke-Splunk {
    param([string[]]$Arguments)
    & $splunkPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Splunk command failed with exit code $LASTEXITCODE"
    }
}

function Set-ClientHostname {
    $inputsPath = "C:\Program Files\SplunkUniversalForwarder\etc\system\local\server.conf"
    $configDir = Split-Path $inputsPath -Parent
    
    if (!(Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }

    $config = "[general]`nserverName = $hostname`n"
    Set-Content -Path $inputsPath -Value $config -Encoding UTF8
    Write-Host "Hostname set to '$hostname' in server.conf" -ForegroundColor Green
}

function Add-ForwardServer {
    Write-Host "Removing Any Existing Forward-Server..." -ForegroundColor Cyan
    try { Invoke-Splunk @("remove", "forward-server", $indexer) } catch { Write-Host "No existing forward-server to remove or removal skipped." -ForegroundColor DarkYellow }
    
    Write-Host "Adding New Forward-Server..." -ForegroundColor Cyan
    Invoke-Splunk @("add", "forward-server", $indexer, "-auth", $login)
}

function Add-Monitors {
    # IIS Logs
    $iisPath = "C:\inetpub\logs\LogFiles\W3SVC1"
    if (Test-Path $iisPath -PathType Container) {
        Write-Host "Adding IIS logs monitor..." -ForegroundColor Cyan
        Invoke-Splunk @("add", "monitor", $iisPath, "-index", "main", "-sourcetype", "iis")
    } else {
        Write-Host "Error: IIS logs path does not exist" -ForegroundColor Red
        Start-Sleep -Seconds 3
    }

    # Windows Event Logs
    $eventPath = "C:\Windows\System32\winevt\Logs"
    if (Test-Path $eventPath -PathType Container) {
        Write-Host "Adding Windows Event Logs..." -ForegroundColor Cyan
        Invoke-Splunk @("add", "monitor", "C:\Windows\System32\winevt\Logs\*.evtx", "-index", "main", "-sourcetype", "WinEventLog")
    } else {
        Write-Host "Error: Windows Event Logs directory does not exist" -ForegroundColor Red
        Start-Sleep -Seconds 3
    }
}

function Restart-Splunk {
    Write-Host "Restarting Splunk Universal Forwarder..." -ForegroundColor Cyan
    Invoke-Splunk @("restart")
}

function Show-Status {
    Write-Host "Waiting 15 seconds for Splunk UF to reconnect..." -ForegroundColor Cyan
    Start-Sleep -Seconds 15
    Invoke-Splunk @("list", "forward-server")
    Invoke-Splunk @("list", "monitor")
}

# --- 4. Execution Flow ---
try {
    Add-ForwardServer
    Set-ClientHostname
    Restart-Splunk
    Add-Monitors
    Restart-Splunk
    Show-Status
    Write-Host "`nSetup and configuration completed successfully!" -ForegroundColor Green
}
catch {
    Write-Error "An error occurred during configuration: $_"
}
