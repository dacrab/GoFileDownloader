from argparse import ArgumentParser, Namespace

DOWNLOAD_FOLDER = "Downloads"
URLS_FILE = "URLs.txt"
GOFILE_API = "https://api.gofile.io"
GOFILE_API_ACCOUNTS = f"{GOFILE_API}/accounts"
MAX_WORKERS = 3
CHUNK_SIZE = 64 * 1024

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "gzip",
    "Accept": "*/*",
    "Connection": "keep-alive",
}


def parse_arguments(*, common_only: bool = False) -> Namespace:
    parser = ArgumentParser(description="GoFile Downloader")
    if not common_only:
        parser.add_argument("url", type=str, help="The URL to process")
        parser.add_argument(
            "password", nargs="?", type=str, help="The password for the download."
        )
    parser.add_argument(
        "--custom-path", type=str, default=None, help="Custom download directory"
    )
    parser.add_argument(
        "--version", action="version", version="GoFile Downloader v2.0.0"
    )
    return parser.parse_args()
