import json
import os
import subprocess
import threading
import queue
from pathlib import Path


class YtDlpDownloader:
    def __init__(self):
        self.process = None
        self.progress_queue = queue.Queue()
        self._stop_event = threading.Event()

    def fetch_video_info(self, url):
        try:
            result = subprocess.run(
                ["yt-dlp", "--js-runtimes", "deno", "--dump-json", "--no-download", url],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"error": "Request timed out"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse video info"}
        except Exception as e:
            return {"error": str(e)}

    def start_download(self, url, output_path, format_choice="best", extra_args=None):
        self._stop_event.clear()
        self.last_filename = None
        self.video_title = None
        self.video_resolution = None
        thread = threading.Thread(
            target=self._run_download,
            args=(url, output_path, format_choice, extra_args or []),
            daemon=True,
        )
        thread.start()
        return thread

    def _run_download(self, url, output_path, format_choice, extra_args):
        output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")

        cmd = [
            "yt-dlp",
            "-f",
            format_choice,
            "--js-runtimes",
            "deno",
            "--merge-output-format",
            "mp4",
            "--continue",
            "--no-overwrites",
            "--fragment-retries",
            "10",
            "--retries",
            "5",
            "--newline",
            "--output",
            output_template,
        ]

        cmd.extend(extra_args)
        cmd.append(url)

        import re

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            for line in self.process.stdout:
                if self._stop_event.is_set():
                    self.process.terminate()
                    self.progress_queue.put({"status": "cancelled"})
                    return

                line = line.strip()
                if not line:
                    continue

                # Parse progress lines like: [download]  50.0% of ~  10.00MiB at  500.00KiB/s ETA 00:10
                if "[download]" in line and "%" in line:
                    pct_match = re.search(r"(\d+\.?\d*)%", line)
                    speed_match = re.search(r"at\s+([^\s]+)", line)
                    eta_match = re.search(r"ETA\s+(\S+)", line)

                    if pct_match:
                        pct = pct_match.group(1)
                        speed = speed_match.group(1) if speed_match else ""
                        eta = eta_match.group(1) if eta_match else ""
                        self.progress_queue.put({
                            "status": "progress",
                            "progress": f"{pct}%",
                            "speed": speed,
                            "eta": eta,
                        })

                elif "Downloading" in line or "Extracting" in line:
                    self.progress_queue.put({"status": "message", "text": line})
                elif "[download] 100%" in line or "100% of" in line:
                    self.progress_queue.put({"status": "message", "text": "Finalizing..."})
                elif "[download] Destination:" in line:
                    self.last_filename = line.split("Destination:", 1)[1].strip()
                elif "[Merger] Merging formats into" in line:
                    self.last_filename = line.split("into ", 1)[1].strip().strip('"')
                elif "[download] " in line and "has already been downloaded" in line:
                    match = re.search(r"\[download\] (.+?) has already been downloaded", line)
                    if match:
                        self.last_filename = match.group(1).strip()

            return_code = self.process.wait()
            if return_code == 0:
                self.progress_queue.put({
                    "status": "completed",
                    "filename": self.last_filename,
                    "title": "",
                    "resolution": "",
                })
            else:
                self.progress_queue.put({"status": "error", "code": return_code})

        except Exception as e:
            self.progress_queue.put({"status": "error", "message": str(e)})

    def stop(self):
        self._stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()

    @staticmethod
    def get_available_formats(url):
        try:
            result = subprocess.run(
                ["yt-dlp", "-F", url],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception:
            return None

    @staticmethod
    def find_yt_dlp():
        for name in ["yt-dlp", "yt-dlp.exe"]:
            for path in os.environ.get("PATH", "").split(os.pathsep):
                full = os.path.join(path, name)
                if os.path.isfile(full):
                    return full
        return None
