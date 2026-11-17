# Run from an Administrator PowerShell only when connected to your own hotspot.
param([Parameter(Mandatory=$true)][string]$LaptopIP, [switch]$Remove)
$ErrorActionPreference = 'Stop'
$ruleName = 'Squat Counter - private phone camera'
if ($Remove) {
    Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Write-Host 'Squat camera firewall rule removed.'
    exit
}
$address = Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -eq $LaptopIP
if (-not $address) { throw 'This IP is not assigned to this laptop. Check ipconfig after joining the hotspot.' }
$profile = Get-NetConnectionProfile -InterfaceIndex $address.InterfaceIndex
if ($profile.NetworkCategory -ne 'Private') {
    throw 'Set ONLY your own hotspot connection to Private in Windows Wi-Fi properties, then retry.'
}
$pythonPath = Join-Path (Split-Path -Parent $PSScriptRoot) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Project Python environment is missing.' }
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
$basePython = (& $pythonPath -c 'import sys; print(sys._base_executable)').Trim()
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $basePython)) { throw 'Could not identify the Python runtime.' }
foreach ($program in (@($pythonPath, $basePython) | Select-Object -Unique)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080,8443 -LocalAddress $LaptopIP -RemoteAddress LocalSubnet -Profile Private -Program $program | Out-Null
}
Write-Host 'Allowed Python launcher/runtime, this local IP, local subnet, Private profile, TCP 8080/8443.'
Write-Host 'No router settings were changed. The certificate listener closes after 10 minutes.'
