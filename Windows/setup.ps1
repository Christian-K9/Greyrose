#Requires -RunAsAdministrator

$forwarder = "splunkforwarder-10.0.1-c486717c322b-windows-x64.msi"
$url = "https://download.splunk.com/products/universalforwarder/releases/10.0.1/windows/$forwarder"
$installDir = "C:\Program Files\SplunkUniversalForwarder"
$localConfigDir = "$installDir\etc\system\local"

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
    # AGREETOLICENSE=Yes is required for quiet installations (/qn)
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

# --- 2. Prompt for Inputs ---
Write-Host "`n--- Splunk Configuration ---" -ForegroundColor Yellow
$server = Read-Host "What is the Server IP?"
$port = Read-Host "What is the Server Receiving Port (e.g., 9997)?"
$indexer = "$server`:$port"
$hostname = Read-Host "Enter a hostname for this client"

# --- 3. Write Splunk Configuration Files ---
try {
    Write-Host "`nConfiguring Splunk files directly..." -ForegroundColor Cyan

    if (!(Test-Path $localConfigDir)) {
        New-Item -ItemType Directory -Path $localConfigDir -Force | Out-Null
    }

    # server.conf (Hostname)
    $serverConf = @"
[general]
serverName = $hostname
"@
    Set-Content -Path "$localConfigDir\server.conf" -Value $serverConf -Encoding UTF8
    Write-Host "Configured server.conf" -ForegroundColor Green

    # outputs.conf (Forwarding Target)
    $outputsConf = @"
[tcpout]
defaultGroup = primary_indexers

[tcpout:primary_indexers]
server = $indexer
"@
    Set-Content -Path "$localConfigDir\outputs.conf" -Value $outputsConf -Encoding UTF8
    Write-Host "Configured outputs.conf" -ForegroundColor Green

    # inputs.conf (Monitors and Host Override)
    $inputsConf = @"
[default]
host = $hostname

"@

    # IIS Logs Check
    $iisPath = "C:\inetpub\logs\LogFiles\W3SVC1"
    if (Test-Path $iisPath -PathType Container) {
        $inputsConf += @"
[monitor://$iisPath]
disabled = false
index = main
sourcetype = iis

"@
        Write-Host "Added IIS log monitor stanza" -ForegroundColor Green
    } else {
        Write-Host "Warning: IIS logs path ($iisPath) not found; skipping IIS monitor." -ForegroundColor DarkYellow
    }

    # Windows Event Logs Check
    $eventPath = "C:\Windows\System32\winevt\Logs"
    if (Test-Path $eventPath -PathType Container) {
        $inputsConf += @"
[monitor://$eventPath\*.evtx]
disabled = false
index = main
sourcetype = WinEventLog

"@
        Write-Host "Added Windows Event Log monitor stanza" -ForegroundColor Green
    } else {
        Write-Host "Warning: Event log directory not found; skipping Event Log monitor." -ForegroundColor DarkYellow
    }

    Set-Content -Path "$localConfigDir\inputs.conf" -Value $inputsConf -Encoding UTF8
    Write-Host "Configured inputs.conf" -ForegroundColor Green
}
catch {
    Write-Error "Failed to write configuration files: $_"
    exit
}

# --- 4. Restart Splunk Service ---
try {
    Write-Host "`nRestarting SplunkForwarder Service..." -ForegroundColor Cyan
    Restart-Service -Name "SplunkForwarder" -ErrorAction Stop
    Write-Host "SplunkForwarder service restarted successfully!" -ForegroundColor Green
    Write-Host "`nSetup complete! Log files, event logs, and target settings are active." -ForegroundColor Green
}
catch {
    Write-Error "Failed to restart SplunkForwarder service: $_"
}
