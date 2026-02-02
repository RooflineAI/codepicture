"""A simple task queue with priority support."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(order=True)
class Task:
    priority: Priority
    name: str = field(compare=False)
    callback: Callable[[], Any] = field(compare=False, repr=False)

    def execute(self) -> Any:
        """Run the task callback and return its result."""
        return self.callback()


class TaskQueue:
    """Priority-based task queue with FIFO ordering within priority levels."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._completed: int = 0

    def enqueue(
        self,
        name: str,
        callback: Callable[[], Any],
        priority: Priority = Priority.NORMAL,
    ) -> None:
        """Add a task to the queue."""
        task = Task(priority=priority, name=name, callback=callback)
        self._tasks.append(task)
        self._tasks.sort(reverse=True)

    def dequeue(self) -> Task | None:
        """Remove and return the highest priority task."""
        if not self._tasks:
            return None
        return self._tasks.pop(0)

    def process_all(self) -> list[Any]:
        """Execute all tasks in priority order and return results."""
        results = []
        while task := self.dequeue():
            results.append(task.execute())
            self._completed += 1
        return results

    @property
    def pending(self) -> int:
        return len(self._tasks)

    @property
    def completed(self) -> int:
        return self._completed
