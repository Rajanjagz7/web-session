<#
  Runs the FakeStoreAPI load test in non-GUI mode and generates an HTML report.
  Usage:
    .\run-load-test.ps1                                  # defaults: 50 users, 60s ramp-up, 360s duration
    .\run-load-test.ps1 -Threads 10 -RampUp 10 -Duration 30   # smoke run
#>
param(
  [int]$Threads = 50,
  [int]$RampUp = 60,
  [int]$Duration = 360,
  [string]$JMeterBin = "jmeter"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$resultsFile = "results\results-$timestamp.jtl"
$reportDir = "reports\html-report-$timestamp"

Write-Host "Running load test: Threads=$Threads RampUp=${RampUp}s Duration=${Duration}s"

& $JMeterBin -n `
  -t "test-plans\fakestoreapi-load-test.jmx" `
  -JTHREADS=$Threads `
  -JRAMPUP=$RampUp `
  -JDURATION=$Duration `
  -l $resultsFile `
  -e -o $reportDir

if ($LASTEXITCODE -ne 0) {
  Write-Error "JMeter run failed with exit code $LASTEXITCODE"
  exit $LASTEXITCODE
}

Write-Host "Results: $resultsFile"
Write-Host "HTML report: $reportDir\index.html"
