import customtkinter as ctk
import os
import subprocess
import threading


class DownloadItem(ctk.CTkFrame):
    def __init__(self, parent, url, downloader, output_path, format_choice, extra_args, main_window):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)

        self.url = url
        self.downloader = downloader
        self.output_path = output_path
        self.format_choice = format_choice
        self.extra_args = extra_args
        self.main_window = main_window
        self.is_downloading = False
        self.downloaded_filename = None
        self.video_title = None
        self.video_resolution = None
        self.display_title = "Fetching title..."

        self._build_ui()
        self._fetch_title_then_start()

    def _build_ui(self):
        # Row 0: Title + action button
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(3, 1))
        top_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            top_frame,
            text=self.display_title,
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.action_btn = ctk.CTkButton(
            top_frame,
            text="Cancel",
            width=50,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#da3633",
            hover_color="#f85149",
            command=self._cancel,
        )
        self.action_btn.grid(row=0, column=1, padx=(6, 0))

        # Row 1: Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(1, 2))
        self.progress_bar.set(0)

        # Row 2: Status + speed
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 3))

        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Starting...",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        )
        self.status_label.pack(side="left")

        self.speed_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e",
        )
        self.speed_label.pack(side="right")

    def _fetch_title_then_start(self):
        def _fetch():
            info = self.downloader.fetch_video_info(self.url)
            if isinstance(info, dict) and "title" in info:
                self.display_title = info["title"][:60] + ("..." if len(info["title"]) > 60 else "")
                self.after(0, lambda: self.title_label.configure(text=self.display_title))
            self.after(0, self._start)

        threading.Thread(target=_fetch, daemon=True).start()

    def _start(self):
        self.is_downloading = True
        thread = self.downloader.start_download(
            self.url,
            self.output_path,
            self.format_choice,
            self.extra_args,
        )
        threading.Thread(target=self._monitor_progress, daemon=True).start()

    def _monitor_progress(self):
        while self.is_downloading:
            try:
                data = self.downloader.progress_queue.get(timeout=0.5)
                self.after(0, lambda d=data: self._update_ui(d))
                if data.get("status") in ("completed", "error", "cancelled"):
                    break
            except Exception:
                continue

    def _update_ui(self, data):
        status = data.get("status")

        if status == "progress":
            try:
                pct = data.get("progress", "0%").replace("%", "").strip()
                if pct:
                    value = float(pct) / 100
                    self.progress_bar.set(value)
            except (ValueError, TypeError):
                pass

            speed = data.get("speed", "")
            eta = data.get("eta", "")
            parts = []
            if speed and speed != "None":
                parts.append(speed)
            if eta and eta != "None":
                parts.append(f"ETA: {eta}")
            if parts:
                self.speed_label.configure(text=" | ".join(parts))

        elif status == "message":
            text = data.get("text", "")
            self.status_label.configure(text=text)
            if "[download] Resuming download at byte" in text:
                self.status_label.configure(text="Resuming...", text_color="#f0883e")

        elif status == "completed":
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Complete", text_color="#2ea043")
            self.speed_label.configure(text="")
            if data.get("filename"):
                self.downloaded_filename = data["filename"]
            if data.get("title"):
                self.video_title = data["title"]
            if data.get("resolution"):
                self.video_resolution = data["resolution"]
            self.action_btn.configure(
                text="Open",
                state="normal",
                fg_color="#2ea043",
                hover_color="#3fb950",
                command=self._show_in_explorer,
            )
            self.is_downloading = False
            filepath = self.downloaded_filename or ""
            if not filepath and self.output_path:
                filepath = self.output_path
            self.main_window.on_download_complete(
                self.url,
                self.video_title or self.url,
                filepath,
                self.video_resolution,
            )

        elif status == "error":
            self.status_label.configure(text=f"Error: {data.get('message', 'Unknown')}", text_color="#da3633")
            self.action_btn.configure(text="Error", state="disabled", fg_color="gray")
            self.is_downloading = False

        elif status == "cancelled":
            self.status_label.configure(text="Cancelled", text_color="#f0883e")
            self.action_btn.configure(text="Cancelled", state="disabled", fg_color="gray")
            self.is_downloading = False

    def _cancel(self):
        if self.is_downloading:
            self.downloader.stop()
            self.is_downloading = False

    def _show_in_explorer(self):
        if self.downloaded_filename and os.path.isfile(self.downloaded_filename):
            subprocess.Popen(f'explorer /select,"{self.downloaded_filename}"')
        elif os.path.isdir(self.output_path):
            os.startfile(self.output_path)
        else:
            self.status_label.configure(text="File not found", text_color="#da3633")
