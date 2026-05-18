# AGENTS

**Quick start**
- Run the app in development with `python main.py`. Use the provided `yt-dlp-gui.bat` on Windows – it adds `C:\yt-dlp` and the user deno bin to `PATH` before launching.
- Required external binaries: `yt-dlp.exe`, `ffmpeg.exe`, `deno.exe`. `yt-dlp-gui.bat` expects them in `C:\yt-dlp` (or any folder on `PATH`). The portable build script downloads them automatically.

**Configuration**
- `config.json` and `history.json` live in the repository root. `utils/config.py` resolves the path relative to the `utils` package (`../config.json`).
- Settings UI mirrors these keys: `output_path`, `format`, `embed_thumbnail`, `embed_subtitles`, `download_subtitles`, `subtitle_langs`, `restrict_filenames`, `max_downloads`, `theme`.
- Changing a setting updates `config.json` via `Config.set()` – no manual file edit needed.

**Building portable distribution**
- Execute `python build_portable.py`. It runs PyInstaller (`--onefile --windowed`) and then creates a portable folder under `dist/yt-dlp-gui-portable`.
- The script ensures required binaries are present; it extracts `ffmpeg.exe` from the official zip and copies `yt-dlp.exe` and `deno.exe`.
- After a successful build, run `Compress-Archive -Path "dist/yt-dlp-gui-portable" -DestinationPath "dist/yt-dlp-gui-portable.zip"` in PowerShell to create a zip.

**Downloading videos**
- The core downloader invokes `yt-dlp` with:
  ```
  yt-dlp -f <format> --js-runtimes deno --merge-output-format mp4 --continue --no-overwrites \
    --fragment-retries 10 --retries 5 --newline --progress-template "{...}" --output "<output_path>/%(title)s [%(id)s].%(ext)s" <url>
  ```
- Extra args from the Settings window are appended verbatim: `--embed-thumbnail`, `--embed-subs`, `--sub-langs <langs>`, `--restrict-filenames`.
- Video info is fetched with `yt-dlp --js-runtimes deno --dump-json --no-download <url>`.

**Common pitfalls**
- If `yt-dlp` is not found on `PATH`, the UI shows a warning but the download will still fail. Ensure `yt-dlp.exe` is in a folder added by `yt-dlp-gui.bat` or manually update `PATH`.
- `deno` is required for JavaScript runtimes; missing it causes subtitle download failures.
- The app uses PowerShell to send Windows toast notifications. On non‑Windows systems the call silently fails.
- `max_downloads` is stored in the config but not enforced by the code – adjusting it alone does not limit concurrency.

**Extending the UI**
- New settings belong in `ui/settings.py` – add a widget in the appropriate tab and sync it in `_save_and_close()`.
- To expose a new downloader flag, add it to the `extra_args` list construction in `MainWindow._start_download()`.

**Running without build**
- The repository is not a Python package; imports rely on the repo root being on `PYTHONPATH`. `main.py` adds its directory to `sys.path` before importing UI modules.

**Dependencies**
- Python ≥3.11 (based on compiled `.pyc` files)
- `customtkinter` (install via `pip install customtkinter`)
- `yt-dlp` binary must be available – pip's `yt-dlp` package is *not* used.
