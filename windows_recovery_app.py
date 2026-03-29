#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Media Recovery App

A focused data recovery utility for images, videos, and ZIP files.
It supports:
- Quick undelete-style recovery from a selected folder/recycle area
- Raw file carving from disk image files (.img/.dd/.raw/.bin)

Notes:
- Raw carving can recover data even when metadata is gone, but filenames/paths
  are usually not preserved.
- For safety, recovered files are always written to a separate output folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


@dataclass
class RecoveryResult:
    file_type: str
    output_path: str
    size_bytes: int
    source_offset: int
    sha1: str


class MediaCarver:
    """Carves image/video/zip files from a byte stream using signatures."""

    TARGET_EXTENSIONS = {
        "jpg": ".jpg",
        "png": ".png",
        "gif": ".gif",
        "bmp": ".bmp",
        "webp": ".webp",
        "zip": ".zip",
        "mp4": ".mp4",
        "mov": ".mov",
        "avi": ".avi",
        "mkv": ".mkv",
    }

    def __init__(self, logger):
        self.logger = logger

    def carve_from_image(
        self,
        image_path: Path,
        output_dir: Path,
        selected_types: set[str],
        max_file_size_mb: int,
        stop_event: threading.Event,
    ) -> list[RecoveryResult]:
        output_dir.mkdir(parents=True, exist_ok=True)
        blob = image_path.read_bytes()
        results: list[RecoveryResult] = []

        self.logger(f"Loaded image source: {image_path} ({len(blob):,} bytes)")
        max_size = max_file_size_mb * 1024 * 1024

        if "jpg" in selected_types:
            results.extend(self._carve_jpeg(blob, output_dir, max_size, stop_event))
        if "png" in selected_types:
            results.extend(self._carve_png(blob, output_dir, max_size, stop_event))
        if "gif" in selected_types:
            results.extend(self._carve_gif(blob, output_dir, max_size, stop_event))
        if "bmp" in selected_types:
            results.extend(self._carve_bmp(blob, output_dir, max_size, stop_event))
        if "webp" in selected_types:
            results.extend(self._carve_webp(blob, output_dir, max_size, stop_event))
        if "zip" in selected_types:
            results.extend(self._carve_zip(blob, output_dir, max_size, stop_event))
        if {"mp4", "mov"} & selected_types:
            results.extend(self._carve_mp4_family(blob, output_dir, max_size, stop_event, selected_types))
        if "avi" in selected_types:
            results.extend(self._carve_avi(blob, output_dir, max_size, stop_event))
        if "mkv" in selected_types:
            results.extend(self._carve_mkv(blob, output_dir, max_size, stop_event))

        return self._dedupe(results)

    def _dedupe(self, items: list[RecoveryResult]) -> list[RecoveryResult]:
        seen: set[str] = set()
        out: list[RecoveryResult] = []
        for item in items:
            if item.sha1 in seen:
                try:
                    Path(item.output_path).unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            seen.add(item.sha1)
            out.append(item)
        return out

    def _persist(self, data: bytes, ext: str, out_dir: Path, offset: int) -> RecoveryResult:
        digest = hashlib.sha1(data).hexdigest()
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        out_file = out_dir / f"recovered_{ext}_{ts}_{offset}{self.TARGET_EXTENSIONS[ext]}"
        out_file.write_bytes(data)
        return RecoveryResult(
            file_type=ext,
            output_path=str(out_file),
            size_bytes=len(data),
            source_offset=offset,
            sha1=digest,
        )

    def _carve_jpeg(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        start, end = b"\xff\xd8\xff", b"\xff\xd9"
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(start, idx)
            if s == -1:
                break
            e = blob.find(end, s + 3)
            if e == -1:
                break
            e += 2
            if 0 < e - s <= max_size:
                results.append(self._persist(blob[s:e], "jpg", out_dir, s))
            idx = e
        self.logger(f"JPEG recovered: {len(results)}")
        return results

    def _carve_png(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        start, end = b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82"
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(start, idx)
            if s == -1:
                break
            e = blob.find(end, s + 8)
            if e == -1:
                break
            e += len(end)
            if 0 < e - s <= max_size:
                results.append(self._persist(blob[s:e], "png", out_dir, s))
            idx = e
        self.logger(f"PNG recovered: {len(results)}")
        return results

    def _carve_gif(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s1 = blob.find(b"GIF87a", idx)
            s2 = blob.find(b"GIF89a", idx)
            starts = [p for p in (s1, s2) if p != -1]
            if not starts:
                break
            s = min(starts)
            e = blob.find(b"\x3b", s + 6)
            if e == -1:
                break
            e += 1
            if 0 < e - s <= max_size:
                results.append(self._persist(blob[s:e], "gif", out_dir, s))
            idx = e
        self.logger(f"GIF recovered: {len(results)}")
        return results

    def _carve_bmp(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(b"BM", idx)
            if s == -1 or s + 6 > len(blob):
                break
            size = int.from_bytes(blob[s + 2:s + 6], "little", signed=False)
            if 64 <= size <= max_size and s + size <= len(blob):
                results.append(self._persist(blob[s:s + size], "bmp", out_dir, s))
                idx = s + size
            else:
                idx = s + 2
        self.logger(f"BMP recovered: {len(results)}")
        return results

    def _carve_webp(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(b"RIFF", idx)
            if s == -1 or s + 12 > len(blob):
                break
            if blob[s + 8:s + 12] != b"WEBP":
                idx = s + 4
                continue
            size = int.from_bytes(blob[s + 4:s + 8], "little", signed=False) + 8
            if 12 <= size <= max_size and s + size <= len(blob):
                results.append(self._persist(blob[s:s + size], "webp", out_dir, s))
                idx = s + size
            else:
                idx = s + 4
        self.logger(f"WEBP recovered: {len(results)}")
        return results

    def _carve_zip(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        end_sig = b"PK\x05\x06"
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(b"PK\x03\x04", idx)
            if s == -1:
                break
            eocd = blob.find(end_sig, s + 4)
            if eocd == -1:
                idx = s + 4
                continue
            e = eocd + 22
            if 0 < e - s <= max_size:
                results.append(self._persist(blob[s:e], "zip", out_dir, s))
            idx = e
        self.logger(f"ZIP recovered: {len(results)}")
        return results

    def _carve_mp4_family(
        self,
        blob: bytes,
        out_dir: Path,
        max_size: int,
        stop_event: threading.Event,
        selected_types: set[str],
    ) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            ftyp = blob.find(b"ftyp", idx)
            if ftyp == -1 or ftyp < 4:
                break
            box_start = ftyp - 4
            size = int.from_bytes(blob[box_start:ftyp], "big", signed=False)
            if size <= 0:
                idx = ftyp + 4
                continue
            mdat = blob.find(b"mdat", ftyp)
            if mdat == -1 or mdat < 4:
                idx = ftyp + 4
                continue
            mdat_size = int.from_bytes(blob[mdat - 4:mdat], "big", signed=False)
            approx_end = max(box_start + size, mdat + mdat_size)
            if approx_end <= box_start or approx_end > len(blob):
                idx = ftyp + 4
                continue
            ext = "mov" if blob[ftyp + 4:ftyp + 8] in {b"qt  ", b"M4V ", b"isom"} and "mov" in selected_types else "mp4"
            if ext not in selected_types:
                ext = "mp4"
            data = blob[box_start:approx_end]
            if 0 < len(data) <= max_size:
                results.append(self._persist(data, ext, out_dir, box_start))
            idx = approx_end
        self.logger(f"MP4/MOV recovered: {len(results)}")
        return results

    def _carve_avi(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(b"RIFF", idx)
            if s == -1 or s + 12 > len(blob):
                break
            if blob[s + 8:s + 12] != b"AVI ":
                idx = s + 4
                continue
            size = int.from_bytes(blob[s + 4:s + 8], "little", signed=False) + 8
            if 12 <= size <= max_size and s + size <= len(blob):
                results.append(self._persist(blob[s:s + size], "avi", out_dir, s))
                idx = s + size
            else:
                idx = s + 4
        self.logger(f"AVI recovered: {len(results)}")
        return results

    def _carve_mkv(self, blob: bytes, out_dir: Path, max_size: int, stop_event: threading.Event) -> list[RecoveryResult]:
        results: list[RecoveryResult] = []
        header = b"\x1a\x45\xdf\xa3"
        idx = 0
        while idx < len(blob) and not stop_event.is_set():
            s = blob.find(header, idx)
            if s == -1:
                break
            next_s = blob.find(header, s + 4)
            e = next_s if next_s != -1 else len(blob)
            if 1024 <= e - s <= max_size:
                results.append(self._persist(blob[s:e], "mkv", out_dir, s))
            idx = e
        self.logger(f"MKV recovered: {len(results)}")
        return results


class WindowsRecoveryApp(tk.Tk):
    """Simple Windows-focused GUI for media recovery."""

    def __init__(self):
        super().__init__()
        self.title("Windows Media Recovery App")
        self.geometry("980x720")
        self.minsize(880, 620)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None

        self._build_ui()
        self.after(150, self._drain_logs)

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            root,
            text="Recover Images, Videos, and ZIP files from folders or disk images",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        mode_frame = ttk.LabelFrame(root, text="Recovery Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=6)
        self.mode_var = tk.StringVar(value="image_carve")
        ttk.Radiobutton(mode_frame, text="Raw Carve from Disk Image", value="image_carve", variable=self.mode_var).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="Folder Recovery Scan (existing files)", value="folder_scan", variable=self.mode_var).grid(row=0, column=1, sticky="w", padx=18)

        paths = ttk.LabelFrame(root, text="Paths", padding=10)
        paths.pack(fill=tk.X, pady=6)

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.home() / "Desktop" / "Recovered_Media"))

        ttk.Label(paths, text="Source (folder or disk image):").grid(row=0, column=0, sticky="w")
        ttk.Entry(paths, textvariable=self.source_var, width=84).grid(row=1, column=0, sticky="we", padx=(0, 8), pady=4)
        ttk.Button(paths, text="Browse", command=self._pick_source).grid(row=1, column=1, sticky="e")

        ttk.Label(paths, text="Output folder:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(paths, textvariable=self.output_var, width=84).grid(row=3, column=0, sticky="we", padx=(0, 8), pady=4)
        ttk.Button(paths, text="Browse", command=self._pick_output).grid(row=3, column=1, sticky="e")
        paths.columnconfigure(0, weight=1)

        filters = ttk.LabelFrame(root, text="Target File Types", padding=10)
        filters.pack(fill=tk.X, pady=6)

        self.type_vars: dict[str, tk.BooleanVar] = {}
        labels = ["jpg", "png", "gif", "bmp", "webp", "mp4", "mov", "avi", "mkv", "zip"]
        for i, ext in enumerate(labels):
            var = tk.BooleanVar(value=True)
            self.type_vars[ext] = var
            ttk.Checkbutton(filters, text=ext.upper(), variable=var).grid(row=i // 5, column=i % 5, padx=8, pady=2, sticky="w")

        opts = ttk.LabelFrame(root, text="Options", padding=10)
        opts.pack(fill=tk.X, pady=6)
        self.max_size_var = tk.StringVar(value="512")
        ttk.Label(opts, text="Max recovered file size (MB):").grid(row=0, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.max_size_var, width=10).grid(row=0, column=1, sticky="w", padx=(8, 0))

        actions = ttk.Frame(root)
        actions.pack(fill=tk.X, pady=6)
        self.start_btn = ttk.Button(actions, text="Start Recovery", command=self._start_recovery)
        self.start_btn.pack(side=tk.LEFT)
        ttk.Button(actions, text="Stop", command=self._stop_recovery).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Open Output", command=self._open_output).pack(side=tk.LEFT)

        self.progress_var = tk.StringVar(value="Idle")
        ttk.Label(root, textvariable=self.progress_var, foreground="#1f4b99").pack(anchor="w", pady=(4, 4))

        logs_frame = ttk.LabelFrame(root, text="Activity Log", padding=6)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        self.log_widget = scrolledtext.ScrolledText(logs_frame, height=18, wrap=tk.WORD)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _pick_source(self):
        if self.mode_var.get() == "image_carve":
            file_path = filedialog.askopenfilename(
                title="Select disk image file",
                filetypes=[("Disk image", "*.img *.dd *.raw *.bin"), ("All files", "*.*")],
            )
            if file_path:
                self.source_var.set(file_path)
        else:
            folder = filedialog.askdirectory(title="Select folder to scan")
            if folder:
                self.source_var.set(folder)

    def _pick_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_var.set(folder)

    def _log(self, text: str):
        self.log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    def _drain_logs(self):
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_widget.insert(tk.END, line + "\n")
            self.log_widget.see(tk.END)
        self.after(150, self._drain_logs)

    def _start_recovery(self):
        source = Path(self.source_var.get().strip())
        output = Path(self.output_var.get().strip())
        if not source.exists():
            messagebox.showerror("Invalid source", "Please pick an existing source path.")
            return

        selected_types = {k for k, v in self.type_vars.items() if v.get()}
        if not selected_types:
            messagebox.showerror("No file types selected", "Select at least one file type.")
            return

        try:
            max_size_mb = int(self.max_size_var.get().strip())
            if max_size_mb <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid max size", "Max size must be a positive integer (MB).")
            return

        self.stop_event.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.progress_var.set("Running recovery...")
        self._log("Recovery job started")

        self.worker_thread = threading.Thread(
            target=self._run_recovery,
            args=(source, output, selected_types, max_size_mb),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_recovery(self, source: Path, output: Path, selected_types: set[str], max_size_mb: int):
        started = time.time()
        output.mkdir(parents=True, exist_ok=True)
        results: list[RecoveryResult] = []

        try:
            if self.mode_var.get() == "image_carve":
                carver = MediaCarver(self._log)
                results = carver.carve_from_image(source, output, selected_types, max_size_mb, self.stop_event)
            else:
                results = self._recover_from_folder(source, output, selected_types, max_size_mb)

            report_path = output / f"recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            payload = {
                "source": str(source),
                "output": str(output),
                "mode": self.mode_var.get(),
                "selected_types": sorted(selected_types),
                "count": len(results),
                "duration_seconds": round(time.time() - started, 2),
                "results": [r.__dict__ for r in results],
            }
            report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self._log(f"Report saved: {report_path}")
            self._log(f"Recovery finished. Files recovered: {len(results)}")
            self.progress_var.set(f"Completed: {len(results)} recovered")
        except Exception as exc:
            self._log(f"Error: {exc}")
            self.progress_var.set("Recovery failed")
        finally:
            self.start_btn.config(state=tk.NORMAL)

    def _recover_from_folder(
        self,
        source: Path,
        output: Path,
        selected_types: set[str],
        max_size_mb: int,
    ) -> list[RecoveryResult]:
        """Copy matching files from folder as a quick recovery workflow."""
        results: list[RecoveryResult] = []
        allowed_suffixes = {MediaCarver.TARGET_EXTENSIONS[k] for k in selected_types}
        max_size = max_size_mb * 1024 * 1024

        for path in source.rglob("*"):
            if self.stop_event.is_set():
                self._log("Recovery canceled by user")
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in allowed_suffixes:
                continue
            try:
                size = path.stat().st_size
                if size <= 0 or size > max_size:
                    continue
                data = path.read_bytes()
                sha1 = hashlib.sha1(data).hexdigest()
                out_file = output / f"recovered_existing_{sha1[:12]}{path.suffix.lower()}"
                if not out_file.exists():
                    out_file.write_bytes(data)
                results.append(
                    RecoveryResult(
                        file_type=path.suffix.lower().lstrip("."),
                        output_path=str(out_file),
                        size_bytes=size,
                        source_offset=-1,
                        sha1=sha1,
                    )
                )
            except OSError as err:
                self._log(f"Skipped {path}: {err}")

        self._log(f"Folder scan recovered: {len(results)}")
        return results

    def _stop_recovery(self):
        self.stop_event.set()
        self._log("Stop requested")

    def _open_output(self):
        out = self.output_var.get().strip()
        if out:
            os.startfile(out) if os.name == "nt" else messagebox.showinfo("Open Output", f"Output folder: {out}")


def main():
    app = WindowsRecoveryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
