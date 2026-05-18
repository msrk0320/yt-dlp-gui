import json
import os
from datetime import datetime
from pathlib import Path


class HistoryManager:
    def __init__(self, history_path=None):
        if history_path is None:
            history_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history.json")
        self.history_path = history_path
        self.entries = self._load()

    def _load(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def save(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save history: {e}")

    def add(self, url, title, filepath, resolution=None, format_choice=None):
        entry = {
            "url": url,
            "title": title,
            "filepath": filepath,
            "resolution": resolution,
            "format": format_choice,
            "timestamp": datetime.now().isoformat(),
        }
        self.entries.insert(0, entry)
        self.save()

    def get_all(self):
        return self.entries

    def remove(self, index):
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            self.save()

    def clear(self):
        self.entries = []
        self.save()

    def exists(self, url):
        return any(e.get("url") == url for e in self.entries)
