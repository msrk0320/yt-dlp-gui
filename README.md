# yt-dlp GUI

A minimalistic, modern desktop GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp) built with Python and CustomTkinter.

## Features

- **Simple URL input** - Paste any video or playlist URL to download
- **Playlist support** - Choose to download single video or entire playlist
- **Format selection** - Best quality, audio-only, or specific resolutions (1080p, 720p, 480p)
- **Subtitle support** - Download and embed subtitles in multiple languages
- **Thumbnail embedding** - Embed video thumbnails into downloaded files
- **Download history** - Track and re-download previous videos
- **Windows notifications** - Desktop toast notifications on download complete
- **Dark theme** - Modern dark UI with CustomTkinter

## Requirements

- **Python** >= 3.11
- **yt-dlp** - [Download](https://github.com/yt-dlp/yt-dlp#installation)
- **ffmpeg** - [Download](https://ffmpeg.org/download.html)
- **deno** - [Download](https://deno.land/) (for JavaScript runtimes)
- **customtkinter** - Install via `pip install customtkinter`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/yt-dlp-gui.git
   cd yt-dlp-gui
   ```

2. Install Python dependencies:
   ```bash
   pip install customtkinter
   ```

3. Ensure `yt-dlp.exe`, `ffmpeg.exe`, and `deno.exe` are in your `PATH` or in `C:\yt-dlp`.

## Usage

### Quick Start

Run the application:
```bash
python main.py
```

Or on Windows, use the provided batch file:
```
yt-dlp-gui.bat
```

### Building Portable Distribution

Create a standalone executable:
```bash
python build_portable.py
```

This creates a portable folder under `dist/yt-dlp-gui-portable` with all required binaries.

To create a zip archive:
```powershell
Compress-Archive -Path "dist/yt-dlp-gui-portable" -DestinationPath "dist/yt-dlp-gui-portable.zip"
```

## Configuration

Settings are stored in `config.json` (created on first run). Available options:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_path` | string | `~/Downloads` | Default download folder |
| `format` | string | `bestvideo+bestaudio/best` | yt-dlp format selector |
| `embed_thumbnail` | bool | `false` | Embed thumbnail in video |
| `embed_subtitles` | bool | `false` | Embed subtitles in video |
| `download_subtitles` | bool | `false` | Download subtitle files |
| `subtitle_langs` | list | `["en"]` | Subtitle language codes |
| `restrict_filenames` | bool | `false` | ASCII-only filenames |
| `max_downloads` | int | `3` | Max concurrent downloads |
| `theme` | string | `"dark"` | UI theme |

## Project Structure

```
yt-dlp-gui/
├── main.py              # Application entry point
├── config.json          # User configuration (gitignored)
── history.json         # Download history (gitignored)
├── yt-dlp-gui.bat       # Windows launcher
├── build_portable.py    # Portable build script
├── core/
│   └── downloader.py    # yt-dlp download engine
├── ui/
│   ├── main_window.py   # Main application window
│   ├── download_item.py # Individual download item widget
│   ── settings.py      # Settings dialog
└── utils/
    ├── config.py        # Configuration manager
    ├── history.py       # History manager
    └── notifications.py # Windows toast notifications
```

## License

MIT License - see [LICENSE](LICENSE) for details.
