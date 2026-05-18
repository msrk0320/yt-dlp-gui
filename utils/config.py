import json
import os
from pathlib import Path


class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self.config_path = config_path
        self.defaults = {
            "output_path": str(Path.home() / "Downloads"),
            "format": "bestvideo+bestaudio/best",
            "embed_thumbnail": False,
            "embed_subtitles": False,
            "download_subtitles": False,
            "subtitle_langs": ["en"],
            "restrict_filenames": False,
            "max_downloads": 3,
            "theme": "dark",
        }
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    loaded = json.load(f)
                return {**self.defaults, **loaded}
            except (json.JSONDecodeError, IOError):
                pass
        return self.defaults.copy()

    def save(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Failed to save config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
