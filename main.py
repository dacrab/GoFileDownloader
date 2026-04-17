import os
import sys
from pathlib import Path

from downloader import Downloader
from src.config import URLS_FILE, parse_arguments
from src.ui import UI


def main() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    args = parse_arguments(common_only=True)

    urls_path = Path(URLS_FILE)
    if not urls_path.exists():
        print("No URLs.txt found")
        return

    urls = [url.strip() for url in urls_path.read_text().splitlines() if url.strip()]
    if not urls:
        print("No URLs found in URLs.txt")
        return

    ui = UI()
    try:
        with ui.live:
            for url in urls:
                Downloader(url, ui, args).initialize_download()
            ui.stop()
    except KeyboardInterrupt:
        sys.exit(1)

    urls_path.write_text("")


if __name__ == "__main__":
    main()
