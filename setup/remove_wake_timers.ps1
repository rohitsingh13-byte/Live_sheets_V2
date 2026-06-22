# Removes all Live Sheets V2 wake timer tasks.
# Run as Administrator.

$slots = @("0930", "1100", "1330", "1600")

Write-Host "Removing Live Sheets V2 wake timers..." -ForegroundColor Yellow
foreach ($s in $slots) {
    $name = "LiveSheets_V2_Wake_$s"
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "  Removed: $name" -ForegroundColor Gray
}
Write-Host "Done." -ForegroundColor Cyan
