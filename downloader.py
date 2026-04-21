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
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn
from rich.table import Table

API = "https://api.gofile.io"
TOKEN_CACHE = Path.home() / ".cache" / "gofile_token"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "gzip",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def get_token():
    """Get GoFile account token (cached or from env var)."""
    # Check environment variable first
    if env_token := os.getenv("GOFILE_TOKEN"):
        return env_token

    # Try cached token
    if TOKEN_CACHE.exists():
        cached = TOKEN_CACHE.read_text(encoding="utf-8").strip()
        if cached:
            return cached

    # Create new token
    r = requests.post(f"{API}/accounts", headers=HEADERS, timeout=15).json()
    if r["status"] == "error-rateLimit":
        print("Error: GoFile API rate limit. Try again later or set GOFILE_TOKEN env var.")
        sys.exit(1)
    if r["status"] != "ok":
        print(f"Error: {r['status']}")
        sys.exit(1)

    token = r["data"]["token"]

    # Cache token
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(token, encoding="utf-8")

    return token


def gen_web_token(token):
    """Generate website token from account token."""
    t = str(int(time()) // 14400)
    seed = f"Mozilla/5.0::en-US::{token}::{t}::5d4f7g8sd45fsd"
    return hashlib.sha256(seed.encode()).hexdigest()


def get_content(content_id, token, password=None):
    """Get content metadata from GoFile API."""
    url = f"{API}/contents/{content_id}"
    url += "?cache=true&sortField=createTime&sortDirection=1"
    if password:
        url += f"&password={password}"
    headers = HEADERS | {
        "Authorization": f"Bearer {token}",
        "X-Website-Token": gen_web_token(token),
        "X-BL": "en-US"
    }
    return requests.get(url, headers=headers, timeout=15).json()


def parse_files(content_id, token, password=None, base_path=None):
    """Parse content and return list of files to download."""
    data = get_content(content_id, token, password)
    if data["status"] != "ok":
        return []

    content = data["data"]
    if "password" in content and content.get("passwordStatus") != "passwordOk":
        return []

    files = []
    if content["type"] == "folder":
        folder = base_path / content["name"] if base_path else Path(content["name"])
        folder.mkdir(parents=True, exist_ok=True)
        for child in content["children"].values():
            if child["type"] == "folder":
                files.extend(parse_files(child["id"], token, password, folder))
            else:
                files.append((folder / child["name"], child["link"]))
    else:
        path = base_path / content["name"] if base_path else Path(content["name"])
        files.append((path, content["link"]))

    return files


def download_file(args):
    """Download a single file with progress tracking."""
    path, url, token, progress, task = args
    if path.exists():
        progress.update(task, visible=False)
        return

    headers = HEADERS | {"Cookie": f"accountToken={token}"}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
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


def main():
    """Main entry point."""
    os.system("cls" if os.name == "nt" else "clear")

    parser = ArgumentParser(description="GoFile Downloader")
    parser.add_argument("url", help="The URL to process")
    parser.add_argument("password", nargs="?", help="The password for the download")
    parser.add_argument("--custom-path", help="Custom download directory")
    parser.add_argument(
        "--version",
        action="version",
        version="GoFileDownloader v1.0.4 by Lysagxra"
    )
    args = parser.parse_args()

    content_id = args.url.rstrip("/").split("/")[-1]
    token = get_token()
    hashed = hashlib.sha256(args.password.encode()).hexdigest()
    password = hashed if args.password else None

    download_path = Path(args.custom_path) if args.custom_path else Path.cwd() / "Downloads"
    download_path.mkdir(exist_ok=True)

    files = parse_files(content_id, token, password, download_path / content_id)
    if not files:
        sys.exit(1)

    overall = Progress(BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%")
    task_progress = Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    )

    overall_task = overall.add_task("", total=len(files))

    table = Table.grid()
    table.add_row(
        Panel(overall, title="Overall Progress", border_style="bright_blue"),
        Panel(task_progress, title="File Progress", border_style="medium_purple"),
    )

    with Live(table, console=Console()):
        tasks = [
            (f, url, token, task_progress, task_progress.add_task(f.name, total=0))
            for f, url in files
        ]
        with ThreadPoolExecutor(max_workers=3) as executor:
            for _ in executor.map(download_file, tasks):
                overall.update(overall_task, advance=1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
