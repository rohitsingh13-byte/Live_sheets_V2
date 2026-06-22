# ─────────────────────────────────────────────────────────────────────────────
# Live Sheets V2 — Windows Wake Timer Setup
#
# Run this script ONCE, as Administrator, to create Task Scheduler entries
# that wake your PC from sleep 15 minutes before each scheduled run.
#
# HOW IT WORKS:
#   Your PC can be in sleep mode (S3). This script creates tasks that tell
#   Windows "wake up at 09:15 so the 09:30 job runs on time."
#   GitHub Actions cron fires at the scheduled time. Your self-hosted runner
#   (already awake) picks up the job and runs it — no user interaction needed.
#
# PREREQUISITE — enable wake timers in Windows Power Settings:
#   Control Panel → Power Options → Change plan settings
#   → Change advanced power settings → Sleep
#   → Allow wake timers → Enable (for both On battery and Plugged in)
#   (Or search "Power Options" in Start → find "Allow wake timers")
#
# RUN AS ADMINISTRATOR:
#   Right-click this file → "Run with PowerShell" → approve UAC prompt
# ─────────────────────────────────────────────────────────────────────────────

# Edit these to match the cron times in .github/workflows/refresh.yml
# Format: "HH:MM" in IST
$SCHEDULED_SLOTS  = @("09:30", "11:00", "13:30", "16:00")
$WAKE_BEFORE_MINS = 15

Write-Host ""
Write-Host "Live Sheets V2 — Wake Timer Setup" -ForegroundColor Cyan
Write-Host ("─" * 50) -ForegroundColor DarkGray
Write-Host ""

foreach ($slot in $SCHEDULED_SLOTS) {
    $parts = $slot -split ':'
    $h     = [int]$parts[0]
    $m     = [int]$parts[1] - $WAKE_BEFORE_MINS

    if ($m -lt 0)  { $h -= 1; $m += 60 }
    if ($h -lt 0)  { $h = 23; $m = 60 + $m }

    $wake_time = "{0:D2}:{1:D2}" -f $h, $m
    $task_name = "LiveSheets_V2_Wake_$($slot -replace ':', '')"

    # Remove if already exists
    Unregister-ScheduledTask -TaskName $task_name -Confirm:$false -ErrorAction SilentlyContinue

    $action    = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c echo LiveSheets V2 wake"
    $trigger   = New-ScheduledTaskTrigger -Daily -At $wake_time
    $settings  = New-ScheduledTaskSettingsSet `
                    -WakeToRun $true `
                    -AllowStartIfOnBatteries $true `
                    -DontStopIfGoingOnBatteries $true `
                    -ExecutionTimeLimit "00:01:00" `
                    -StartWhenAvailable $true
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

    $result = Register-ScheduledTask `
                -TaskName  $task_name `
                -Action    $action `
                -Trigger   $trigger `
                -Settings  $settings `
                -Principal $principal `
                -Force 2>&1

    if ($?) {
        Write-Host ("  OK  " + $task_name) -ForegroundColor Green -NoNewline
        Write-Host ("   wakes at $wake_time IST  (15 min before $slot run)") -ForegroundColor Gray
    } else {
        Write-Host ("  FAIL  " + $task_name + ": " + $result) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step — verify 'Allow wake timers' is ON:" -ForegroundColor Yellow
Write-Host "  Win+R → powercfg.cpl → Change plan settings" -ForegroundColor Gray
Write-Host "  → Change advanced power settings → Sleep → Allow wake timers → Enable" -ForegroundColor Gray
Write-Host ""
Write-Host "To remove these tasks later, run:  setup\remove_wake_timers.ps1" -ForegroundColor Gray
Write-Host ""
