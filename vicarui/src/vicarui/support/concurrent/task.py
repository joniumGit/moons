from typing import Dict, NoReturn

from PySide2.QtCore import QThread

from .lock import Lock

_lock = Lock()
_tasks: Dict[int, QThread] = dict()


def _add_task(task: QThread) -> NoReturn:
    task_id = id(task)
    _tasks[task_id] = task
    task.finished.connect(lambda: _lock.run_blocking(lambda: _tasks.pop(task_id)))


class Tasker:

    @staticmethod
    def run(task: QThread) -> NoReturn:
        """
        Runs a task and holds a reference to it until done
        """
        _lock.run_blocking(lambda: _add_task(task))
        task.start(priority=QThread.HighPriority)


__all__ = ['Tasker']
