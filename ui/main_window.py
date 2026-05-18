import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.downloader import YtDlpDownloader
from utils.config import Config
from utils.history import HistoryManager
from utils.notifications import send_notification
import os
import threading


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("yt-dlp GUI")
        self.geometry("700x480")
        self.minsize(580, 350)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config_manager = Config()
        self.history_manager = HistoryManager()
        self.downloader = YtDlpDownloader()
        self.downloads = []
        self.active_downloads = {}

        self._build_ui()
        self._check_yt_dlp()

    def _check_yt_dlp(self):
        if not self.downloader.find_yt_dlp():
            messagebox.showwarning(
                "yt-dlp Not Found",
                "yt-dlp is not installed or not in PATH.\n"
                "Please install it: https://github.com/yt-dlp/yt-dlp",
            )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        # URL input row
        url_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        url_frame.grid(row=0, column=0, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Paste video URL...",
            height=34,
            font=ctk.CTkFont(size=14),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.url_entry.bind("<Return>", lambda e: self._start_download(force_playlist=None))

        self.fetch_btn = ctk.CTkButton(
            url_frame,
            text="Fetch",
            height=34,
            width=55,
            font=ctk.CTkFont(size=13),
            command=self._fetch_info,
        )
        self.fetch_btn.grid(row=0, column=1, padx=(0, 4))

        self.download_btn = ctk.CTkButton(
            url_frame,
            text="Download",
            height=34,
            width=75,
            font=ctk.CTkFont(size=13),
            fg_color="#2ea043",
            hover_color="#3fb950",
            command=self._start_download,
        )
        self.download_btn.grid(row=0, column=2)

        # Settings button - top right
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙",
            width=30,
            height=30,
            font=ctk.CTkFont(size=15),
            command=self._open_settings,
        )
        settings_btn.grid(row=0, column=1, padx=(10, 0))

        # Save path row
        save_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        save_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        save_frame.grid_columnconfigure(0, weight=1)

        self.output_path_var = ctk.StringVar(value=self.config_manager.get("output_path"))
        self.save_path_entry = ctk.CTkEntry(
            save_frame,
            textvariable=self.output_path_var,
            height=28,
            font=ctk.CTkFont(size=12),
            placeholder_text="Save location...",
        )
        self.save_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        btn_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        self.browse_btn = ctk.CTkButton(
            btn_frame,
            text="Browse",
            width=55,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._browse_save_path,
        )
        self.browse_btn.pack(side="left", padx=(0, 3))

        self.open_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Open",
            width=45,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._open_save_folder,
        )
        self.open_folder_btn.pack(side="left")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)

        downloads_tab = self.tabview.add("Downloads")
        downloads_tab.grid_columnconfigure(0, weight=1)
        downloads_tab.grid_rowconfigure(0, weight=1)

        self.download_scroll = ctk.CTkScrollableFrame(downloads_tab)
        self.download_scroll.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.download_scroll.grid_columnconfigure(0, weight=1)

        history_tab = self.tabview.add("History")
        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(0, weight=1)

        history_header = ctk.CTkFrame(history_tab, fg_color="transparent")
        history_header.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        history_header.grid_columnconfigure(0, weight=1)

        self.history_count_label = ctk.CTkLabel(
            history_header,
            text=f"{len(self.history_manager.entries)} downloads",
            font=ctk.CTkFont(size=12),
        )
        self.history_count_label.grid(row=0, column=0, sticky="w")

        clear_btn = ctk.CTkButton(
            history_header,
            text="Clear",
            width=55,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color="#da3633",
            hover_color="#f85149",
            command=self._clear_history,
        )
        clear_btn.grid(row=0, column=1, padx=(4, 0))

        self.history_scroll = ctk.CTkScrollableFrame(history_tab)
        self.history_scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.history_scroll.grid_columnconfigure(0, weight=1)

        self._load_history()

    def _build_status_bar(self):
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color="gray",
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))

    def _load_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        entries = self.history_manager.get_all()
        if not entries:
            ctk.CTkLabel(
                self.history_scroll,
                text="No downloads yet",
                font=ctk.CTkFont(size=12),
                text_color="gray",
            ).pack(pady=30)
            return

        for i, entry in enumerate(entries):
            frame = ctk.CTkFrame(self.history_scroll)
            frame.pack(fill="x", padx=2, pady=2)
            frame.grid_columnconfigure(0, weight=1)

            title = entry.get("title", "Unknown")
            timestamp = entry.get("timestamp", "")
            resolution = entry.get("resolution", "")
            filepath = entry.get("filepath", "")

            info_parts = []
            if resolution:
                info_parts.append(resolution)
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    info_parts.append(dt.strftime("%b %d, %H:%M"))
                except Exception:
                    pass

            ctk.CTkLabel(
                frame,
                text=title[:50] + ("..." if len(title) > 50 else ""),
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=6, pady=(3, 0))

            ctk.CTkLabel(
                frame,
                text=" | ".join(info_parts),
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 3))

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=1, rowspan=2, padx=6, pady=2)

            if filepath and os.path.isfile(filepath):
                open_btn = ctk.CTkButton(
                    btn_frame,
                    text="Open",
                    width=45,
                    height=20,
                    font=ctk.CTkFont(size=10),
                    command=lambda f=filepath: os.startfile(f),
                )
                open_btn.pack(side="left", padx=2)

            folder_btn = ctk.CTkButton(
                btn_frame,
                text="Folder",
                width=45,
                height=20,
                font=ctk.CTkFont(size=10),
                command=lambda f=filepath: os.startfile(os.path.dirname(f) if os.path.isfile(f) else f),
            )
            folder_btn.pack(side="left", padx=2)

            redl_btn = ctk.CTkButton(
                btn_frame,
                text="Re-download",
                width=60,
                height=20,
                font=ctk.CTkFont(size=10),
                command=lambda u=entry.get("url", ""): self._redownload(u),
            )
            redl_btn.pack(side="left", padx=2)

        self.history_count_label.configure(text=f"{len(entries)} downloads")

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Clear all download history?"):
            self.history_manager.clear()
            self._load_history()

    def _redownload(self, url):
        self.tabview.set("Downloads")
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self._start_download(force_playlist=None)

    def _fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a URL")
            return

        self._set_status("Fetching video info...")
        self.fetch_btn.configure(state="disabled")

        def _fetch():
            info = self.downloader.fetch_video_info(url)
            self.after(0, lambda: self._on_info_fetched(info))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_info_fetched(self, info):
        self.fetch_btn.configure(state="normal")
        if "error" in info:
            self._set_status(f"Error: {info['error']}")
            return

        title = info.get("title", "Unknown")
        duration = info.get("duration_string", "Unknown")
        self._set_status(f"Found: {title} ({duration})")

    def _is_playlist_url(self, url):
        playlist_indicators = ["/playlist?", "list=", "/channel/", "/c/", "/user/", "@"]
        return any(indicator in url for indicator in playlist_indicators)

    def _start_download(self, force_playlist=None):
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Please enter a URL")
            return

        output_path = self.output_path_var.get().strip()
        if not output_path or not os.path.isdir(output_path):
            self._set_status("Invalid save location. Please browse to select a folder.")
            return

        if force_playlist is None and self._is_playlist_url(url):
            self._ask_playlist_choice(url, output_path)
            return

        self._do_download(url, output_path, force_playlist)

    def _ask_playlist_choice(self, url, output_path):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Playlist Detected")
        dialog.geometry("320x160")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(
            dialog,
            text="Playlist URL detected. What would you like to do?",
            font=ctk.CTkFont(size=12),
            wraplength=280,
        ).pack(pady=(15, 10), padx=15)

        def do_single():
            dialog.destroy()
            self._do_download(url, output_path, force_playlist=False)

        def do_playlist():
            dialog.destroy()
            self._do_download(url, output_path, force_playlist=True)

        ctk.CTkButton(
            dialog,
            text="Download Single Video",
            width=200,
            height=32,
            command=do_single,
        ).pack(pady=4)

        ctk.CTkButton(
            dialog,
            text="Download Entire Playlist",
            width=200,
            height=32,
            fg_color="#2ea043",
            hover_color="#3fb950",
            command=do_playlist,
        ).pack(pady=4)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def _do_download(self, url, output_path, force_playlist):
        self.config_manager.set("output_path", output_path)
        format_choice = self.config_manager.get("format", "bestvideo+bestaudio/best")

        extra_args = []
        if force_playlist is False:
            extra_args.append("--no-playlist")
        elif force_playlist is True:
            extra_args.append("--yes-playlist")

        if self.config_manager.get("embed_thumbnail"):
            extra_args.append("--embed-thumbnail")
        if self.config_manager.get("embed_subtitles"):
            extra_args.append("--embed-subs")
        if self.config_manager.get("download_subtitles"):
            langs = ",".join(self.config_manager.get("subtitle_langs", ["en"]))
            extra_args.extend(["--sub-langs", langs])
        if self.config_manager.get("restrict_filenames"):
            extra_args.append("--restrict-filenames")

        item = DownloadItem(
            self.download_scroll,
            url,
            self.downloader,
            output_path,
            format_choice,
            extra_args,
            self,
        )
        item.pack(fill="x", padx=2, pady=2)
        self.downloads.append(item)

        self.url_entry.delete(0, "end")
        mode = "playlist" if force_playlist else "video"
        self._set_status(f"Added {mode}: {url[:40]}...")

    def on_download_complete(self, url, title, filepath, resolution):
        self.history_manager.add(url, title, filepath, resolution)
        self._load_history()
        send_notification("Download Complete", title[:80])

    def _open_settings(self):
        settings_window = SettingsWindow(self, self.config_manager)
        self.wait_window(settings_window)

    def _browse_save_path(self):
        folder = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if folder:
            self.output_path_var.set(folder)
            self.config_manager.set("output_path", folder)

    def _open_save_folder(self):
        path = self.output_path_var.get().strip()
        if path and os.path.isdir(path):
            os.startfile(path)
        else:
            self._set_status("Invalid folder path")

    def _set_status(self, text):
        self.status_bar.configure(text=text)


from ui.download_item import DownloadItem
from ui.settings import SettingsWindow
