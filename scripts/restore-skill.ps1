param(
    [string]$BackupName,
    [int]$KeepBackups = 5
)

$ErrorActionPreference = "Stop"

$SkillName = "personal-ai-brain"

$Target = Join-Path $env:USERPROFILE ".codex\skills\$SkillName"
$BackupRoot = Join-Path $env:USERPROFILE ".codex\skill-backups\$SkillName"

if ($KeepBackups -lt 1) {
    throw "KeepBackups must be greater than or equal to 1."
}

Write-Host "Personal AI Brain Skill Restore"
Write-Host "Target      : $Target"
Write-Host "Backup root : $BackupRoot"
Write-Host ""

# --------------------------------------------------
# Validate backup root
# --------------------------------------------------

if (-not (Test-Path $BackupRoot)) {
    throw "Backup directory does not exist: $BackupRoot"
}

$Backups = Get-ChildItem $BackupRoot -Directory |
    Sort-Object Name -Descending

if (-not $Backups) {
    throw "No Skill backups found."
}

# --------------------------------------------------
# Select backup
# --------------------------------------------------

if ($BackupName) {

    $BackupPath = Join-Path $BackupRoot $BackupName

    if (-not (Test-Path $BackupPath)) {
        throw "Backup does not exist: $BackupPath"
    }

}
else {

    $BackupPath = $Backups[0].FullName
    $BackupName = $Backups[0].Name
}

$BackupSkillFile = Join-Path $BackupPath "SKILL.md"

if (-not (Test-Path $BackupSkillFile)) {
    throw "Selected backup is invalid. SKILL.md not found: $BackupPath"
}

Write-Host "Selected backup: $BackupName"
Write-Host ""

# --------------------------------------------------
# Backup current installed version before restore
# --------------------------------------------------

if (Test-Path $Target) {

    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $RollbackBackupName = "$Timestamp-before-restore"
    $RollbackBackupPath = Join-Path $BackupRoot $RollbackBackupName

    Write-Host "Backing up currently installed Skill..."
    Write-Host "Backup path: $RollbackBackupPath"

    Copy-Item `
        -Path $Target `
        -Destination $RollbackBackupPath `
        -Recurse `
        -Force
}

# --------------------------------------------------
# Remove current installation
# --------------------------------------------------

if (Test-Path $Target) {

    Write-Host "Removing current installed Skill..."

    Remove-Item `
        -Path $Target `
        -Recurse `
        -Force
}

# --------------------------------------------------
# Restore selected backup
# --------------------------------------------------

Write-Host "Restoring backup..."

Copy-Item `
    -Path $BackupPath `
    -Destination $Target `
    -Recurse `
    -Force

# --------------------------------------------------
# Verify restore
# --------------------------------------------------

Write-Host "Verifying restored files..."

$Failed = $false

$BackupFiles = Get-ChildItem $BackupPath -Recurse -File

foreach ($File in $BackupFiles) {

    $RelativePath = $File.FullName.Substring($BackupPath.Length)
    $TargetFile = "$Target$RelativePath"

    if (-not (Test-Path $TargetFile)) {

        Write-Host "[MISSING] $RelativePath"
        $Failed = $true
        continue
    }

    $BackupHash = (Get-FileHash $File.FullName -Algorithm SHA256).Hash
    $TargetHash = (Get-FileHash $TargetFile -Algorithm SHA256).Hash

    if ($BackupHash -ne $TargetHash) {

        Write-Host "[MISMATCH] $RelativePath"
        $Failed = $true
    }
    else {

        Write-Host "[OK] $RelativePath"
    }
}

# Also ensure the target has no extra files
$TargetFiles = Get-ChildItem $Target -Recurse -File

foreach ($File in $TargetFiles) {

    $RelativePath = $File.FullName.Substring($Target.Length)
    $BackupFile = "$BackupPath$RelativePath"

    if (-not (Test-Path $BackupFile)) {

        Write-Host "[EXTRA] $RelativePath"
        $Failed = $true
    }
}

if ($Failed) {
    throw "Skill restore verification failed."
}

# --------------------------------------------------
# Backup retention
# Keep newest N backups regardless of backup type
# --------------------------------------------------

$Backups = Get-ChildItem $BackupRoot -Directory |
    Sort-Object Name -Descending

$BackupsToDelete = $Backups | Select-Object -Skip $KeepBackups

foreach ($Backup in $BackupsToDelete) {
    Write-Host "Removing old backup: $($Backup.Name)"

    Remove-Item `
        -Path $Backup.FullName `
        -Recurse `
        -Force
}

Write-Host ""
Write-Host "Personal AI Brain Skill restored successfully."
Write-Host "Restored backup:"
Write-Host $BackupName
Write-Host ""
Write-Host "Installed path:"
Write-Host $Target
