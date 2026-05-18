import customtkinter as ctk
from tkinter import filedialog
import os


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("420x440")
        self.resizable(False, False)

        self.config_manager = config_manager
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tabview = ctk.CTkTabview(self)
        tabview.grid(row=0, column=0, padx=12, pady=(8, 6), sticky="nsew")
        tabview.grid_columnconfigure(0, weight=1)
        tabview.grid_rowconfigure(0, weight=1)

        self._build_general_tab(tabview.add("General"))
        self._build_format_tab(tabview.add("Format"))
        self._build_subtitles_tab(tabview.add("Subtitles"))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(0, 12))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            height=30,
            width=75,
            font=ctk.CTkFont(size=12),
            command=self._save_and_close,
        )
        save_btn.pack(side="left", padx=(0, 6))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            height=30,
            width=75,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            hover_color="#666",
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

    def _build_general_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="Output Folder", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=10, pady=(8, 3), sticky="w"
        )

        self.output_path_var = ctk.StringVar(value=self.config_manager.get("output_path"))
        output_entry = ctk.CTkEntry(
            tab,
            textvariable=self.output_path_var,
            height=28,
            font=ctk.CTkFont(size=12),
        )
        output_entry.grid(row=0, column=1, padx=(6, 4), pady=(8, 3), sticky="ew")

        browse_btn = ctk.CTkButton(
            tab,
            text="Browse",
            width=55,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._browse_folder,
        )
        browse_btn.grid(row=0, column=2, padx=(0, 10), pady=(8, 3))

        ctk.CTkLabel(tab, text="Max Downloads", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, padx=10, pady=6, sticky="w"
        )

        self.max_downloads_var = ctk.IntVar(value=self.config_manager.get("max_downloads", 3))
        max_spinner = ctk.CTkEntry(
            tab,
            textvariable=self.max_downloads_var,
            width=45,
            height=28,
            font=ctk.CTkFont(size=12),
        )
        max_spinner.grid(row=1, column=1, padx=6, pady=6, sticky="w")

    def _build_format_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Quality", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, padx=10, pady=(6, 2), sticky="w"
        )

        self.format_var = ctk.StringVar(value=self.config_manager.get("format", "bestvideo+bestaudio/best"))

        formats = [
            ("Best (Video+Audio)", "bestvideo+bestaudio/best"),
            ("Best Single File", "best"),
            ("Audio Only (MP3)", "bestaudio/best"),
            ("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
            ("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
            ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
        ]

        for i, (label, value) in enumerate(formats, start=1):
            radio = ctk.CTkRadioButton(
                tab,
                text=label,
                variable=self.format_var,
                value=value,
                font=ctk.CTkFont(size=11),
            )
            radio.grid(row=i, column=0, padx=14, pady=1, sticky="w")

        options_frame = ctk.CTkFrame(tab, fg_color="transparent")
        options_frame.grid(row=7, column=0, sticky="w", padx=10, pady=(6, 4))

        self.embed_thumb_var = ctk.BooleanVar(value=self.config_manager.get("embed_thumbnail", False))
        embed_thumb = ctk.CTkCheckBox(
            options_frame,
            text="Embed Thumbnail",
            variable=self.embed_thumb_var,
            font=ctk.CTkFont(size=11),
        )
        embed_thumb.pack(side="left", padx=(0, 10))

        self.restrict_var = ctk.BooleanVar(value=self.config_manager.get("restrict_filenames", False))
        restrict = ctk.CTkCheckBox(
            options_frame,
            text="ASCII Filenames",
            variable=self.restrict_var,
            font=ctk.CTkFont(size=11),
        )
        restrict.pack(side="left")

    def _build_subtitles_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        self.download_subs_var = ctk.BooleanVar(value=self.config_manager.get("download_subtitles", False))
        download_subs = ctk.CTkCheckBox(
            tab,
            text="Download Subtitles",
            variable=self.download_subs_var,
            font=ctk.CTkFont(size=12),
        )
        download_subs.grid(row=0, column=0, padx=10, pady=(8, 3), sticky="w")

        self.embed_subs_var = ctk.BooleanVar(value=self.config_manager.get("embed_subtitles", False))
        embed_subs = ctk.CTkCheckBox(
            tab,
            text="Embed in Video",
            variable=self.embed_subs_var,
            font=ctk.CTkFont(size=12),
        )
        embed_subs.grid(row=1, column=0, padx=10, pady=3, sticky="w")

        ctk.CTkLabel(tab, text="Languages (comma-separated)", font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, padx=10, pady=(8, 3), sticky="w"
        )

        langs = ",".join(self.config_manager.get("subtitle_langs", ["en"]))
        self.langs_var = ctk.StringVar(value=langs)
        langs_entry = ctk.CTkEntry(
            tab,
            textvariable=self.langs_var,
            height=28,
            font=ctk.CTkFont(size=12),
            placeholder_text="en,ja,ko",
        )
        langs_entry.grid(row=3, column=0, padx=10, pady=3, sticky="ew")

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if folder:
            self.output_path_var.set(folder)

    def _save_and_close(self):
        self.config_manager.set("output_path", self.output_path_var.get())
        self.config_manager.set("format", self.format_var.get())
        self.config_manager.set("embed_thumbnail", self.embed_thumb_var.get())
        self.config_manager.set("embed_subtitles", self.embed_subs_var.get())
        self.config_manager.set("download_subtitles", self.download_subs_var.get())
        self.config_manager.set("restrict_filenames", self.restrict_var.get())
        self.config_manager.set("max_downloads", self.max_downloads_var.get())

        langs = [l.strip() for l in self.langs_var.get().split(",") if l.strip()]
        self.config_manager.set("subtitle_langs", langs)

        self.destroy()
