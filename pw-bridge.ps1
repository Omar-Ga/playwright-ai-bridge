# pw-bridge.ps1
# Usage: pw-bridge.ps1 click e15

$argsList = $args
$session = "default"

# Extract -s=xxx or --session=xxx if passed
$filteredArgs = @()
foreach ($arg in $argsList) {
    if ($arg -like "-s=*") {
        $session = $arg.Substring(3)
    } elseif ($arg -like "--session=*") {
        $session = $arg.Substring(10)
    } else {
        $filteredArgs += $arg
    }
}

$body = @{
    args = $filteredArgs
    session = $session
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8080/cli" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 180
    
    if ($null -ne $response.stdout) {
        # Using Write-Host to avoid standard output piping issues in PowerShell
        # Or Write-Output depending on what's better. We'll use [Console]::Write to be precise.
        [Console]::Out.Write($response.stdout)
    }
    if ($null -ne $response.stderr) {
        [Console]::Error.Write($response.stderr)
    }
    exit $response.returncode
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
