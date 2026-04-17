import asyncio
import hashlib
import os
import sys
from argparse import Namespace
from pathlib import Path

import httpx

from src.config import BASE_HEADERS, DOWNLOAD_FOLDER, MAX_WORKERS, parse_arguments
from src.download_utils import save_file_with_progress
from src.gofile_utils import (
    generate_content_url,
    generate_website_token,
    get_account_token,
    get_content_id,
)
from src.ui import UI


class Downloader:
    def __init__(self, url: str, ui: UI, args: Namespace | None = None) -> None:
        self.url = url
        self.ui = ui
        self.password = args.password if args and hasattr(args, "password") else None
        self.download_path = (
            Path(args.custom_path)
            if args and args.custom_path
            else Path.cwd() / DOWNLOAD_FOLDER
        )
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.token = get_account_token()

    async def download_item(
        self, client: httpx.AsyncClient, current_task: int, file_info: dict[str, str]
    ) -> None:
        filename = file_info["filename"]
        final_path = Path(file_info["download_path"]) / filename

        if final_path.exists():
            self.ui.log("Skipped", f"{filename} exists")
            return

        headers = BASE_HEADERS.copy()
        headers["Cookie"] = f"accountToken={self.token}"

        try:
            async with client.stream(
                "GET", file_info["download_link"], headers=headers, timeout=30.0
            ) as response:
                if response.is_success:
                    task_id = self.ui.add_task(current_task=current_task)
                    await save_file_with_progress(
                        response, final_path, task_id, self.ui
                    )
        except httpx.TimeoutException:
            self.ui.log("Timeout", f"{filename} timed out")
        except Exception as e:
            self.ui.log("Error", f"{filename}: {e}")

    def parse_links(
        self,
        identifier: str,
        files_info: list[dict[str, str]],
        password: str | None = None,
        base_path: Path | None = None,
    ) -> None:
        if base_path is None:
            base_path = self.download_path / identifier
            base_path.mkdir(parents=True, exist_ok=True)

        headers = BASE_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        headers["X-Website-Token"] = generate_website_token(self.token)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    generate_content_url(identifier, password), headers=headers
                )
                data = response.json()
        except Exception as e:
            self.ui.log("Error", f"Request failed: {str(e)[:50]}")
            return

        if data["status"] != "ok":
            error_msg = str(data.get("data", "Unknown error"))[:50]
            self.ui.log("Failed", f"{identifier}: {error_msg}")
            return

        content = data["data"]
        if "password" in content and content.get("passwordStatus") != "passwordOk":
            self.ui.log("Password required", "Invalid password")
            return

        if content["type"] == "folder":
            folder_path = base_path / content["name"]
            folder_path.mkdir(parents=True, exist_ok=True)

            for child in content["children"].values():
                if child["type"] == "folder":
                    self.parse_links(child["id"], files_info, password, folder_path)
                else:
                    files_info.append(
                        {
                            "download_path": str(folder_path),
                            "filename": child["name"],
                            "download_link": child["link"],
                        }
                    )
        else:
            files_info.append(
                {
                    "download_path": str(base_path),
                    "filename": content["name"],
                    "download_link": content["link"],
                }
            )

    async def download_all(self, files_info: list[dict[str, str]]) -> None:
        async with httpx.AsyncClient(
            limits=httpx.Limits(max_connections=MAX_WORKERS)
        ) as client:
            tasks = [
                self.download_item(client, i, file_info)
                for i, file_info in enumerate(files_info)
            ]
            await asyncio.gather(*tasks)

    def initialize_download(self) -> None:
        content_id = get_content_id(self.url)
        if not content_id:
            return

        files_info: list[dict[str, str]] = []
        hashed_password = (
            hashlib.sha256(self.password.encode()).hexdigest()
            if self.password
            else None
        )
        self.parse_links(content_id, files_info, hashed_password)

        if not files_info:
            return

        self.ui.add_overall_task(description=content_id, num_tasks=len(files_info))
        asyncio.run(self.download_all(files_info))


def main() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    args = parse_arguments()
    ui = UI()

    try:
        with ui.live:
            Downloader(args.url, ui, args).initialize_download()
            ui.stop()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
