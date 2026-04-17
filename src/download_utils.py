from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from rich.progress import TaskID

from .config import CHUNK_SIZE

if TYPE_CHECKING:
    from .ui import UI


async def save_file_with_progress(
    response: httpx.Response, download_path: Path, task: TaskID, ui: "UI"
) -> None:
    file_size = int(response.headers.get("Content-Length", -1))
    if file_size == -1:
        return

    total_downloaded = 0
    with download_path.open("wb") as file:
        async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
            file.write(chunk)
            total_downloaded += len(chunk)
            ui.update_task(task, completed=(total_downloaded / file_size) * 100)
