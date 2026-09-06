param(
    [int]$KeepBackups = 5
)

$ErrorActionPreference = "Stop"

$SkillName = "personal-ai-brain"

$Source = Join-Path $PSScriptRoot "..\skills\$SkillName"
$Target = Join-Path $env:USERPROFILE ".codex\skills\$SkillName"
$BackupRoot = Join-Path $env:USERPROFILE ".codex\skill-backups\$SkillName"

$Source = [System.IO.Path]::GetFullPath($Source)

Write-Host "Personal AI Brain Skill Installer"
Write-Host "Source      : $Source"
Write-Host "Target      : $Target"
Write-Host "Backup root : $BackupRoot"
Write-Host ""

# --------------------------------------------------
# Validate source
# --------------------------------------------------

if (-not (Test-Path $Source)) {
    throw "Skill source directory does not exist: $Source"
}

$SkillFile = Join-Path $Source "SKILL.md"

if (-not (Test-Path $SkillFile)) {
    throw "SKILL.md does not exist: $SkillFile"
}

if ($KeepBackups -lt 1) {
    throw "KeepBackups must be greater than or equal to 1."
}

# --------------------------------------------------
# Ensure target / backup parent directories exist
# --------------------------------------------------

$TargetParent = Split-Path $Target -Parent

if (-not (Test-Path $TargetParent)) {
    New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
}

if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
}

# --------------------------------------------------
# Backup current installed Skill
# --------------------------------------------------

if (Test-Path $Target) {
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $BackupName = "$Timestamp-install"
    $BackupPath = Join-Path $BackupRoot $BackupName

    Write-Host "Backing up current installed Skill..."
    Write-Host "Backup path : $BackupPath"

    Copy-Item `
        -Path $Target `
        -Destination $BackupPath `
        -Recurse `
        -Force
}

# --------------------------------------------------
# Install clean copy
# --------------------------------------------------

if (Test-Path $Target) {
    Write-Host "Removing current installed Skill..."

    Remove-Item `
        -Path $Target `
        -Recurse `
        -Force
}

Write-Host "Installing Skill..."

Copy-Item `
    -Path $Source `
    -Destination $Target `
    -Recurse `
    -Force

# --------------------------------------------------
# Verify installed files
# --------------------------------------------------

Write-Host "Verifying installed files..."

$Failed = $false
$SourceFiles = Get-ChildItem $Source -Recurse -File

foreach ($File in $SourceFiles) {
    $RelativePath = $File.FullName.Substring($Source.Length)
    $TargetFile = "$Target$RelativePath"

    if (-not (Test-Path $TargetFile)) {
        Write-Host "[MISSING]  $RelativePath"
        $Failed = $true
        continue
    }

    $SourceHash = (Get-FileHash $File.FullName -Algorithm SHA256).Hash
    $TargetHash = (Get-FileHash $TargetFile -Algorithm SHA256).Hash

    if ($SourceHash -ne $TargetHash) {
        Write-Host "[MISMATCH] $RelativePath"
        $Failed = $true
    }
    else {
        Write-Host "[OK]       $RelativePath"
    }
}

# Also ensure the target has no extra files
$TargetFiles = Get-ChildItem $Target -Recurse -File

foreach ($File in $TargetFiles) {
    $RelativePath = $File.FullName.Substring($Target.Length)
    $SourceFile = "$Source$RelativePath"

    if (-not (Test-Path $SourceFile)) {
        Write-Host "[EXTRA]    $RelativePath"
        $Failed = $true
    }
}

if ($Failed) {
    throw "Skill installation verification failed."
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

# --------------------------------------------------
# Done
# --------------------------------------------------

Write-Host ""
Write-Host "Personal AI Brain Skill installed successfully."
Write-Host "Installed path : $Target"

if (Test-Path $BackupRoot) {
    Write-Host "Backups kept   : $KeepBackups"
    Write-Host "Backup root    : $BackupRoot"
}