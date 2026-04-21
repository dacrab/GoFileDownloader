#!/usr/bin/env python3
"""Batch downloader for multiple GoFile URLs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.live import Live
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, DownloadColumn, TransferSpeedColumn
)

from downloader import get_token, parse_files, download_file

urls = Path("URLs.txt").read_text(encoding="utf-8").strip().split("\n")
token = get_token()
progress = Progress(
    SpinnerColumn(),
    *Progress.get_default_columns(),
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn()
)

with Live(progress):
    for url in urls:
        content_id = url.split("/")[-1]
        files = parse_files(content_id, token, base_path=Path("Downloads"))
        tasks = [
            (f, u, token, progress, progress.add_task(f.name, total=0))
            for f, u in files
        ]
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(download_file, tasks)
