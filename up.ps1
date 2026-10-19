# Sets a new Upstox access token on both Vercel projects and redeploys them.
# Usage:  powershell -File update-upstox-token.ps1
# Use an *extended* token (valid ~1 year) so this is a once-a-year job.
$ErrorActionPreference = "Stop"
$secure = Read-Host "Paste the new UPSTOX_ACCESS_TOKEN" -AsSecureString
$token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
if ($token.Length -lt 100) { throw "That doesn't look like an Upstox access token." }

foreach ($proj in "rajanstocks", "rajantrading") {
    Push-Location (Join-Path $PSScriptRoot $proj)
    try {
        Write-Host "Updating $proj ..."
        $token | vercel env add UPSTOX_ACCESS_TOKEN production --force | Out-Null
        vercel deploy --prod --yes | Select-String "Aliased"
    } finally { Pop-Location }
}
$token = $null
Write-Host "Done. Check https://rajanstocks.vercel.app/api/m/quotes?symbols=NIFTY"
