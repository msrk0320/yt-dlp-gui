import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
import tempfile

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(APP_DIR, "dist")
BUILD_DIR = os.path.join(APP_DIR, "build")
PORTABLE_DIR = os.path.join(DIST_DIR, "yt-dlp-gui-portable")

REQUIRED_BINARIES = {
    "yt-dlp.exe": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
    "ffmpeg.exe": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "deno.exe": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip",
}


def download_file(url, dest):
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, dest)
    print(f"  -> {dest}")


def extract_zip(zip_path, extract_dir, target_file):
    print(f"Extracting {target_file} from {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(target_file) or name == target_file:
                zf.extract(name, extract_dir)
                src = os.path.join(extract_dir, name)
                dst = os.path.join(extract_dir, target_file)
                if src != dst:
                    shutil.move(src, dst)
                return dst
    return None


def ensure_binary(name, download_url, output_dir):
    dest = os.path.join(output_dir, name)
    if os.path.isfile(dest):
        print(f"  {name} already exists")
        return dest

    tmp = tempfile.mkdtemp()
    try:
        if download_url.endswith(".zip"):
            zip_path = os.path.join(tmp, "download.zip")
            download_file(download_url, zip_path)
            result = extract_zip(zip_path, tmp, name)
            if result:
                shutil.copy(result, dest)
                return dest
        else:
            download_file(download_url, dest)
            return dest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return None


def run_pyinstaller():
    print("\n=== Building with PyInstaller ===")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--windowed",
            "--name",
            "yt-dlp-gui",
            "--icon=NONE",
            "--add-data",
            f"ui{os.pathsep}ui",
            "--add-data",
            f"core{os.pathsep}core",
            "--add-data",
            f"utils{os.pathsep}utils",
            "--hidden-import",
            "customtkinter",
            "--collect-all",
            "customtkinter",
            os.path.join(APP_DIR, "main.py"),
        ],
        cwd=APP_DIR,
        check=True,
    )


def create_portable():
    print("\n=== Creating Portable Distribution ===")

    if os.path.exists(PORTABLE_DIR):
        shutil.rmtree(PORTABLE_DIR)
    os.makedirs(PORTABLE_DIR, exist_ok=True)

    exe_src = os.path.join(DIST_DIR, "yt-dlp-gui.exe")
    if os.path.isfile(exe_src):
        shutil.copy(exe_src, os.path.join(PORTABLE_DIR, "yt-dlp-gui.exe"))
        print("  Copied yt-dlp-gui.exe")
    else:
        print(f"  ERROR: {exe_src} not found!")
        return False

    for name, url in REQUIRED_BINARIES.items():
        ensure_binary(name, url, PORTABLE_DIR)

    bat_content = """@echo off
start "" "%~dp0yt-dlp-gui.exe"
"""
    with open(os.path.join(PORTABLE_DIR, "Run.bat"), "w") as f:
        f.write(bat_content)

    readme = """yt-dlp GUI - Portable Edition
================================

Requirements:
- Windows 10 or later
- Internet connection

Included:
- yt-dlp.exe (video downloader)
- ffmpeg.exe (video merger/converter)
- deno.exe (JavaScript runtime for YouTube)

Usage:
1. Double-click Run.bat or yt-dlp-gui.exe
2. Paste a YouTube URL
3. Click Download

Settings are stored in config.json and history.json in the same folder.

For issues: https://github.com/yt-dlp/yt-dlp
"""
    with open(os.path.join(PORTABLE_DIR, "README.txt"), "w") as f:
        f.write(readme)

    print("\n=== Portable distribution ready ===")
    print(f"  Location: {PORTABLE_DIR}")
    return True


def main():
    print("=== yt-dlp GUI Build Script ===\n")

    os.chdir(APP_DIR)

    run_pyinstaller()

    if create_portable():
        print("\nBuild complete!")
        print(f"\nTo create a distributable zip, run:")
        print(f"  Compress-Archive -Path '{PORTABLE_DIR}' -DestinationPath '{DIST_DIR}\\yt-dlp-gui-portable.zip'")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
