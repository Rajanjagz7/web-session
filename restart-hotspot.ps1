<#
.SYNOPSIS
    Restarts Windows Mobile Hotspot and ensures it is set to high-speed (Auto / 5 GHz).

.DESCRIPTION
    Stops the hotspot if active, verifies/applies the preferred band (Auto/5GHz), 
    and restarts it cleanly using the Windows Runtime NetworkOperatorTetheringManager API.

.PARAMETER Band
    The network band to use: Auto, FiveGigahertz, or TwoPointFourGigahertz. Default is Auto.

.EXAMPLE
    .\restart-hotspot.ps1
    .\restart-hotspot.ps1 -Band FiveGigahertz
#>

[CmdletBinding()]
param(
    [ValidateSet("Auto", "FiveGigahertz", "TwoPointFourGigahertz")]
    [string]$Band = "Auto"
)

# Load WinRT assemblies and types
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime] | Out-Null
[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime] | Out-Null

# Helper to await WinRT IAsyncOperation
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
})[0]

function Await-WinRtOp($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

Write-Host "=== Windows Mobile Hotspot Restarter ===" -ForegroundColor Cyan

# 1. Get active internet connection profile
$profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
if (-not $profile) {
    Write-Error "No active internet connection found to share."
    exit 1
}

Write-Host "Internet Source Profile: $($profile.ProfileName)" -ForegroundColor Gray

# 2. Initialize tethering manager
$mgr = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
$config = $mgr.GetCurrentAccessPointConfiguration()

# 3. Configure desired Band
$targetBand = [Windows.Networking.NetworkOperators.TetheringWiFiBand]::$Band
if ($config.Band -ne $targetBand) {
    Write-Host "Updating Band from $($config.Band) -> $Band..." -ForegroundColor Yellow
    $config.Band = $targetBand
    $configOp = $mgr.ConfigureAccessPointAsync($config)
    $asActionTask = [System.WindowsRuntimeSystemExtensions]::AsTask($configOp)
    $asActionTask.Wait(-1) | Out-Null
}

# 4. Stop if currently On
if ($mgr.TetheringOperationalState -eq [Windows.Networking.NetworkOperators.TetheringOperationalState]::On) {
    Write-Host "Stopping Mobile Hotspot..." -ForegroundColor Yellow
    $stopOp = $mgr.StopTetheringAsync()
    $stopRes = Await-WinRtOp $stopOp ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
    if ($stopRes.Status -ne "Success") {
        Write-Warning "Stop status: $($stopRes.Status)"
    }
    Start-Sleep -Seconds 2
}

# 5. Start Hotspot
Write-Host "Starting Mobile Hotspot..." -ForegroundColor Yellow
$startOp = $mgr.StartTetheringAsync()
$startRes = Await-WinRtOp $startOp ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])

if ($startRes.Status -eq "Success") {
    Write-Host "[OK] Hotspot started successfully!" -ForegroundColor Green
} else {
    Write-Error "Failed to start hotspot. Status: $($startRes.Status)"
    exit 1
}

# 6. Summary info
$updatedConfig = $mgr.GetCurrentAccessPointConfiguration()
Write-Host "`nHotspot Details:" -ForegroundColor Cyan
Write-Host "  SSID       : $($updatedConfig.Ssid)"
Write-Host "  Band       : $($updatedConfig.Band)"
Write-Host "  State      : $($mgr.TetheringOperationalState)"
Write-Host "=========================================" -ForegroundColor Cyan
