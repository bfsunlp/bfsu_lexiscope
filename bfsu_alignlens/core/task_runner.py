from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class TaskMessage:
    kind: str
    message: str = ''
    progress: float = 0.0
    result: Any = None
    error: str = ''


class TaskRunner:
    def __init__(self):
        self.queue: queue.Queue[TaskMessage] = queue.Queue()
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run(self, func: Callable, *args, **kwargs):
        if self._thread and self._thread.is_alive():
            raise RuntimeError('Another task is already running.')
        self._cancel.clear()

        def progress(message: str, value: float = 0.0):
            self.queue.put(TaskMessage('progress', message=message, progress=float(value)))

        def target():
            try:
                result = func(*args, progress=progress, cancel_event=self._cancel, **kwargs)
                self.queue.put(TaskMessage('done', result=result, progress=1.0))
            except Exception as exc:
                self.queue.put(TaskMessage('error', error=str(exc), message=traceback.format_exc()))

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel.set()
        self.queue.put(TaskMessage('log', message='Cancel requested.'))

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return out
