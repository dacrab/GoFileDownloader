#!/usr/bin/env python3
"""Minimal GoFile downloader with concurrent downloads."""
import hashlib
import os
import sys
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import time

import requests
from rich.live import Live
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn

API = "https://api.gofile.io"
TOKEN_CACHE = Path.home() / ".cache" / "gofile_token"


def get_token():
    """Get or create a GoFile account token."""
    if token := os.getenv("GOFILE_TOKEN"):
        return token
    if TOKEN_CACHE.exists() and (token := TOKEN_CACHE.read_text().strip()):
        return token

    r = requests.post(f"{API}/accounts", timeout=15).json()
    if r["status"] != "ok":
        sys.exit(f"Error: {r['status']}")

    token = r["data"]["token"]
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(token)
    return token


def _wtoken(token):
    """Generate website token."""
    t = str(int(time()) // 14400)
    return hashlib.sha256(f"Mozilla/5.0::en-US::{token}::{t}::5d4f7g8sd45fsd".encode()).hexdigest()


def get_content(content_id, token, password=None):
    """Fetch content metadata from GoFile API."""
    params = "?cache=true&sortField=createTime&sortDirection=1"
    if password:
        params += f"&password={password}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": f"Bearer {token}",
        "X-Website-Token": _wtoken(token),
        "X-BL": "en-US",
    }
    return requests.get(f"{API}/contents/{content_id}{params}", headers=headers, timeout=15).json()


def parse_files(content_id, token, password=None, base_path=None):
    """Recursively parse content, return list of (path, url) tuples."""
    data = get_content(content_id, token, password)
    if data["status"] != "ok":
        return []

    content = data["data"]
    if "password" in content and content.get("passwordStatus") != "passwordOk":
        return []

    files = []
    if content["type"] == "folder":
        folder = (base_path / content["name"]) if base_path else Path(content["name"])
        folder.mkdir(parents=True, exist_ok=True)
        for child in content["children"].values():
            if child["type"] == "folder":
                files.extend(parse_files(child["id"], token, password, folder))
            else:
                files.append((folder / child["name"], child["link"]))
    else:
        path = (base_path / content["name"]) if base_path else Path(content["name"])
        files.append((path, content["link"]))
    return files


def _download(path, url, token, progress, task):
    """Download a single file with progress tracking."""
    if path.exists():
        progress.update(task, visible=False)
        return
    try:
        hdrs = {"Cookie": f"accountToken={token}"}
        with requests.get(url, headers=hdrs, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            progress.update(task, total=total)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    except requests.RequestException:
        progress.update(task, visible=False)


def _run_downloads(files, token):
    """Run concurrent downloads with progress display."""
    progress = Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    )
    with Live(progress), ThreadPoolExecutor(max_workers=3) as pool:
        tasks = [(f, url, token, progress, progress.add_task(f.name, total=0)) for f, url in files]
        pool.map(lambda a: _download(*a), tasks)


def main():
    """CLI entry point."""
    parser = ArgumentParser(description="GoFile Downloader")
    parser.add_argument("url", nargs="?", help="GoFile URL")
    parser.add_argument("password", nargs="?", help="Folder password")
    parser.add_argument("--custom-path", help="Custom download directory")
    parser.add_argument("--batch", type=Path, help="File with URLs (one per line)")
    args = parser.parse_args()

    if not args.url and not args.batch:
        parser.error("provide a URL or --batch file")

    token = get_token()
    dest = Path(args.custom_path) if args.custom_path else Path.cwd() / "Downloads"
    dest.mkdir(exist_ok=True)
    password = hashlib.sha256(args.password.encode()).hexdigest() if args.password else None

    if args.batch:
        if not args.batch.exists():
            sys.exit(f"{args.batch} not found")
        urls = [u for u in args.batch.read_text().strip().splitlines() if u.strip()]
        all_files = []
        for url in urls:
            cid = url.rstrip("/").split("/")[-1]
            all_files.extend(parse_files(cid, token, password, dest / cid))
    else:
        content_id = args.url.rstrip("/").split("/")[-1]
        all_files = parse_files(content_id, token, password, dest / content_id)

    if not all_files:
        sys.exit("No files found (wrong URL or password?)")

    _run_downloads(all_files, token)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
