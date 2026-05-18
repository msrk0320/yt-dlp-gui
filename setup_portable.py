import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.join(SCRIPT_DIR, "portable_env")
BIN_DIR = os.path.join(ENV_DIR, "bin")

PYTHON_VERSION = "3.11.9"
PYTHON_ZIP_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

REQUIRED_BINARIES = {
    "yt-dlp.exe": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
    "ffmpeg.exe": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "deno.exe": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip",
}


def print_step(text):
    print(f"\n=== {text} ===")


def download_file(url, dest):
    print(f"Downloading {os.path.basename(dest)}...")
    urllib.request.urlretrieve(url, dest)


def extract_zip(zip_path, dest_dir):
    print(f"Extracting to {dest_dir}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)


def setup_python():
    print_step("Setting up Portable Python")
    
    if os.path.exists(os.path.join(ENV_DIR, "python.exe")):
        print("Python already installed. Skipping.")
        return

    os.makedirs(ENV_DIR, exist_ok=True)
    
    zip_path = os.path.join(SCRIPT_DIR, "python_embed.zip")
    download_file(PYTHON_ZIP_URL, zip_path)
    extract_zip(zip_path, ENV_DIR)
    os.remove(zip_path)
    
    # Enable site-packages for pip
    pth_file = os.path.join(ENV_DIR, f"python{PYTHON_VERSION.replace('.', '')}._pth")
    if os.path.exists(pth_file):
        with open(pth_file, "r") as f:
            content = f.read()
        if "#import site" in content:
            content = content.replace("#import site", "import site")
            with open(pth_file, "w") as f:
                f.write(content)
            print("Enabled site-packages for pip.")


def install_pip():
    print_step("Installing pip")
    
    pip_script = os.path.join(SCRIPT_DIR, "get-pip.py")
    if not os.path.exists(pip_script):
        download_file(GET_PIP_URL, pip_script)
    
    python_exe = os.path.join(ENV_DIR, "python.exe")
    subprocess.run([python_exe, pip_script], check=True)
    os.remove(pip_script)


def install_dependencies():
    print_step("Installing Dependencies")
    python_exe = os.path.join(ENV_DIR, "python.exe")
    subprocess.run([python_exe, "-m", "pip", "install", "customtkinter"], check=True)


def download_binaries():
    print_step("Downloading Binaries")
    os.makedirs(BIN_DIR, exist_ok=True)
    
    tmp = tempfile.mkdtemp()
    try:
        for name, url in REQUIRED_BINARIES.items():
            dest = os.path.join(BIN_DIR, name)
            if os.path.exists(dest):
                print(f"  {name} already exists. Skipping.")
                continue
            
            if url.endswith(".zip"):
                zip_path = os.path.join(tmp, "bin.zip")
                download_file(url, zip_path)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    for item in zf.namelist():
                        if item.endswith(name) or item == name:
                            zf.extract(item, tmp)
                            src = os.path.join(tmp, item)
                            shutil.move(src, dest)
                            break
                os.remove(zip_path)
            else:
                download_file(url, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def create_launcher():
    print_step("Creating Launcher")
    bat_content = """@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PATH=%SCRIPT_DIR%portable_env\\bin;%SCRIPT_DIR%portable_env;%PATH%"
cd /d "%SCRIPT_DIR%"
portable_env\\python.exe main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    pause
)
"""
    with open(os.path.join(SCRIPT_DIR, "Run.bat"), "w") as f:
        f.write(bat_content)
    print("Created Run.bat")


def main():
    print("=== yt-dlp GUI Portable Setup ===")
    print("This script will download Python and required tools to run the app without installation.")
    
    try:
        setup_python()
        install_pip()
        install_dependencies()
        download_binaries()
        create_launcher()
        
        print("\n=== Setup Complete ===")
        print("You can now run the application by double-clicking 'Run.bat'")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
