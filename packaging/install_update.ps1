$ErrorActionPreference = 'Stop'
$failed = $false
try {
    $owner = Get-Process -Id $update.owner -ErrorAction SilentlyContinue
    if ($owner -and -not $owner.WaitForExit(15000)) { throw 'The running application did not exit.' }
    $setup = Start-Process -FilePath $update.setup -PassThru -ArgumentList @(
        '/SP-', '/SILENT', '/NORESTART', '/PTFUPDATE=1', $update.tasks
    )
    $setup.WaitForExit()
    if ($setup.ExitCode -ne 0) { throw "Setup exited with code $($setup.ExitCode)." }
} catch {
    $failed = $true
} finally {
    Remove-Item -LiteralPath $update.setup -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Split-Path -LiteralPath $update.setup) -Force -ErrorAction SilentlyContinue
}
if ($failed) {
    if ($update.restart -and (Test-Path -LiteralPath $update.restart -PathType Leaf)) {
        Start-Process -FilePath $update.restart -ErrorAction SilentlyContinue
    }
    Add-Type -AssemblyName System.Windows.Forms
    [void][Windows.Forms.MessageBox]::Show(
        'نصب به‌روزرسانی کامل نشد. از منوی کنار ساعت دوباره امتحان کنید.',
        'Persian Typo Fixer', 'OK', 'Error', 'Button1', 'RtlReading, RightAlign'
    )
    exit 1
}
