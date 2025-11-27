# Demo script for Voice Assistant Calendar internal simulation endpoint
# Usage: Run from the repository root in PowerShell
# Example: .\scripts\demo_voice_simulate.ps1

$base = 'http://localhost:5000'
$user = 'tester@local'

function Post-Json($url, $obj) {
    $json = $obj | ConvertTo-Json -Depth 6
    try {
        $resp = Invoke-RestMethod -Uri $url -Method Post -Body $json -ContentType 'application/json'
        return $resp
    } catch {
        Write-Host "ERROR calling $url -- $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "1) Booking a demo event (booking payload)" -ForegroundColor Cyan
$booking = @{ transcript = 'Book a meeting tomorrow at 2 PM called Demo Meeting'; user_id = $user; timezone = 'UTC'; demo = $true }
$r = Post-Json "$base/internal/voice_simulate" $booking
Write-Host "Response:" -ForegroundColor Green
$r | ConvertTo-Json -Depth 6 | Write-Host

Start-Sleep -Milliseconds 400

Write-Host "2) Listing demo events for tomorrow" -ForegroundColor Cyan
$list = @{ transcript = 'Show my events for tomorrow'; user_id = $user; timezone = 'UTC'; demo = $true }
$r2 = Post-Json "$base/internal/voice_simulate" $list
Write-Host "Response:" -ForegroundColor Green
$r2 | ConvertTo-Json -Depth 6 | Write-Host

Start-Sleep -Milliseconds 400

Write-Host "3) Booking a second demo event (optional)" -ForegroundColor Cyan
$booking2 = @{ transcript = 'Schedule Project Sync tomorrow at 4 PM'; user_id = $user; timezone = 'UTC'; demo = $true }
$r3 = Post-Json "$base/internal/voice_simulate" $booking2
Write-Host "Response:" -ForegroundColor Green
$r3 | ConvertTo-Json -Depth 6 | Write-Host

Start-Sleep -Milliseconds 400

Write-Host "4) Listing demo events again (tomorrow)" -ForegroundColor Cyan
$r4 = Post-Json "$base/internal/voice_simulate" $list
Write-Host "Response:" -ForegroundColor Green
$r4 | ConvertTo-Json -Depth 6 | Write-Host

Start-Sleep -Milliseconds 400

Write-Host "5) Cancel the 'Project Sync' event (demo)" -ForegroundColor Cyan
$cancel = @{ transcript = 'Cancel Project Sync tomorrow at 4 PM'; user_id = $user; timezone = 'UTC'; demo = $true }
$rc = Post-Json "$base/internal/voice_simulate" $cancel
Write-Host "Response:" -ForegroundColor Green
$rc | ConvertTo-Json -Depth 6 | Write-Host

Start-Sleep -Milliseconds 400

Write-Host "6) Listing demo events after cancel" -ForegroundColor Cyan
$r5 = Post-Json "$base/internal/voice_simulate" $list
Write-Host "Response:" -ForegroundColor Green
$r5 | ConvertTo-Json -Depth 6 | Write-Host

Write-Host "Demo script completed." -ForegroundColor Magenta
