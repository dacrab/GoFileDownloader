import datetime
import shutil
import time
from collections import deque
from datetime import UTC
from typing import cast

from rich.align import Align
from rich.box import SIMPLE
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

VERSION = "2.0.0"


class UI:
    def __init__(
        self, task_name: str = "Album", item_description: str = "File"
    ) -> None:
        self.task_name = task_name
        self.item_description = item_description
        self.num_tasks = 0
        self.start_time = time.time()

        self.overall_progress = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        self.task_progress = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            " ",
            TimeRemainingColumn(),
        )
        self.log_buffer: deque[tuple[str, str, str]] = deque(maxlen=4)

        self.live = Live(self._render(), refresh_per_second=10)
        self.log("Started", "Script execution started")

    def add_overall_task(self, description: str, num_tasks: int) -> None:
        self.num_tasks = num_tasks
        desc = description[:8] + "..." if len(description) > 8 else description
        self.overall_progress.add_task(
            f"[light_cyan3]{desc}", total=num_tasks, completed=0
        )

    def add_task(self, current_task: int = 0, total: int = 100) -> TaskID:
        desc = (
            f"[light_cyan3]{self.item_description} {current_task + 1}/{self.num_tasks}"
        )
        return self.task_progress.add_task(desc, total=total)

    def update_task(
        self,
        task_id: TaskID,
        completed: float | None = None,
        advance: int = 0,
        *,
        visible: bool = True,
    ) -> None:
        self.task_progress.update(
            task_id,
            completed=completed if completed is not None else None,
            advance=advance if completed is None else None,
            visible=visible,
        )
        if self.task_progress.tasks[cast(int, task_id)].finished:
            self.overall_progress.advance(self.overall_progress.tasks[-1].id)
            self.task_progress.update(task_id, visible=False)

    def log(self, event: str, details: str) -> None:
        timestamp = datetime.datetime.now(UTC).strftime("%H:%M:%S")
        self.log_buffer.append((timestamp, event, details))
        self.live.update(self._render())

    def stop(self) -> None:
        elapsed = time.time() - self.start_time
        td = datetime.timedelta(seconds=elapsed)
        hrs, mins, secs = td.seconds // 3600, (td.seconds % 3600) // 60, td.seconds % 60
        self.log("Completed", f"Time: {hrs:02}:{mins:02}:{secs:02}")
        self.live.stop()

    def _render(self) -> Group:
        terminal_width, _ = shutil.get_terminal_size()
        panel_width = max(30, terminal_width // 2)

        progress_table = Table.grid()
        progress_table.add_row(
            Panel.fit(
                self.overall_progress,
                title="[bold light_cyan3]Overall Progress",
                border_style="cyan",
                padding=(1, 1),
                width=panel_width,
            ),
            Panel.fit(
                self.task_progress,
                title=f"[bold light_cyan3]{self.task_name} Progress",
                border_style="cyan",
                padding=(1, 1),
                width=panel_width,
            ),
        )

        log_table = Table(
            box=SIMPLE,
            show_header=True,
            show_edge=True,
            show_lines=False,
            border_style="light_cyan3",
        )
        log_table.add_column(
            "[light_cyan3]Timestamp", style="pale_turquoise4", width=10
        )
        log_table.add_column("[light_cyan3]Event", style="pale_turquoise1", width=15)
        log_table.add_column("[light_cyan3]Details", style="pale_turquoise4", width=30)
        for row in self.log_buffer:
            log_table.add_row(*row)

        log_panel = Panel.fit(
            log_table,
            title="[bold light_cyan3]Log Messages",
            border_style="cyan",
            width=2 * panel_width,
        )
        footer = Align.left(Text(f"GoFile Downloader v{VERSION}", style="dim"))

        return Group(progress_table, log_panel, footer)
