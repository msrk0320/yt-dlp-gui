# yt-dlp GUI Portable Setup Script
# This script sets up a portable Python environment and downloads required binaries.
# Run this script once. No system Python required.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$EnvDir = Join-Path $ScriptDir "portable_env"
$BinDir = Join-Path $EnvDir "bin"

$PythonVersion = "3.11.9"
$PythonZipUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

$Binaries = @{
    "yt-dlp.exe" = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    "ffmpeg.exe" = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    "deno.exe"   = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
}

function Write-Step {
    param([string]$Text)
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Download-File {
    param([string]$Url, [string]$Dest)
    Write-Host "Downloading $(Split-Path $Dest -Leaf)..."
    Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
}

function Extract-Zip {
    param([string]$ZipPath, [string]$DestDir)
    Write-Host "Extracting to $DestDir..."
    Expand-Archive -Path $ZipPath -DestinationPath $DestDir -Force
}

# Check if already set up
if (Test-Path (Join-Path $EnvDir "python.exe")) {
    Write-Host "Portable Python already installed. Skipping setup." -ForegroundColor Yellow
    exit 0
}

try {
    # 1. Setup Python
    Write-Step "Setting up Portable Python"
    New-Item -ItemType Directory -Force -Path $EnvDir | Out-Null

    $ZipPath = Join-Path $ScriptDir "python_embed.zip"
    Download-File -Url $PythonZipUrl -Dest $ZipPath
    Extract-Zip -ZipPath $ZipPath -DestDir $EnvDir
    Remove-Item $ZipPath

    # Enable site-packages
    $PthFile = Get-ChildItem -Path $EnvDir -Filter "python*._pth" | Select-Object -First 1
    if ($PthFile) {
        $Content = Get-Content $PthFile.FullName
        if ($Content -contains "#import site") {
            $Content = $Content -replace "#import site", "import site"
            Set-Content -Path $PthFile.FullName -Value $Content
            Write-Host "Enabled site-packages for pip."
        }
    }

    # 2. Install pip
    Write-Step "Installing pip"
    $GetPipPath = Join-Path $ScriptDir "get-pip.py"
    Download-File -Url $GetPipUrl -Dest $GetPipPath
    
    $PythonExe = Join-Path $EnvDir "python.exe"
    & $PythonExe $GetPipPath
    Remove-Item $GetPipPath

    # 3. Install Dependencies
    Write-Step "Installing Dependencies"
    & $PythonExe -m pip install customtkinter

    # 4. Download Binaries
    Write-Step "Downloading Binaries"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

    $TempDir = Join-Path $EnvDir "temp_bin"
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

    foreach ($Name in $Binaries.Keys) {
        $Url = $Binaries[$Name]
        $Dest = Join-Path $BinDir $Name
        
        if (Test-Path $Dest) {
            Write-Host "  $Name already exists. Skipping."
            continue
        }

        if ($Url.EndsWith(".zip")) {
            $ZipPath = Join-Path $TempDir "bin.zip"
            Download-File -Url $Url -Dest $ZipPath
            Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force
            Remove-Item $ZipPath

            # Find the extracted exe and move it
            $ExtractedExe = Get-ChildItem -Path $TempDir -Recurse -Filter $Name | Select-Object -First 1
            if ($ExtractedExe) {
                Move-Item -Path $ExtractedExe.FullName -Destination $Dest
            }
        } else {
            Download-File -Url $Url -Dest $Dest
        }
    }
    Remove-Item $TempDir -Recurse -Force

    # 5. Create Launcher
    Write-Step "Creating Launcher"
    $BatContent = @"
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PATH=%SCRIPT_DIR%portable_env\bin;%SCRIPT_DIR%portable_env;%PATH%"
cd /d "%SCRIPT_DIR%"
portable_env\python.exe main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    pause
)
"@
    Set-Content -Path (Join-Path $ScriptDir "Run.bat") -Value $BatContent
    Write-Host "Created Run.bat"

    Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
    Write-Host "You can now run the application by double-clicking 'Run.bat'"
}
catch {
    Write-Host "`nError: $_" -ForegroundColor Red
    exit 1
}
