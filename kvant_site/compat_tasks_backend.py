"""
Custom django-tasks backend compatible with Python 3.12.
Fixes: TypeError when instantiating frozen generic dataclass TaskResult[T].
"""
from copy import deepcopy
from functools import partial

from django.db import transaction
from django.utils import timezone

from django_tasks.backends.base import BaseTaskBackend
from django_tasks.base import Task, TaskResult, TaskResultStatus
from django_tasks.exceptions import TaskResultDoesNotExist
from django_tasks.signals import task_enqueued
from django_tasks.utils import get_random_id


def _make_task_result(task, **kwargs):
    """Create TaskResult without using generic subscript syntax (TaskResult[T])."""
    return TaskResult(task=task, **kwargs)


class Py312CompatBackend(BaseTaskBackend):
    """
    In-memory dummy backend that works with Python 3.12 frozen dataclasses.
    """
    supports_defer = True
    supports_async_task = True
    supports_priority = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.results = []

    def _store_result(self, result):
        object.__setattr__(result, "enqueued_at", timezone.now())
        self.results.append(result)
        task_enqueued.send(type(self), task_result=result)

    def enqueue(self, task, args, kwargs):
        self.validate_task(task)

        result = _make_task_result(
            task=task,
            id=get_random_id(),
            status=TaskResultStatus.READY,
            enqueued_at=None,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=args,
            kwargs=kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

        if self._get_enqueue_on_commit_for_task(task) is not False:
            transaction.on_commit(partial(self._store_result, result))
        else:
            self._store_result(result)

        return deepcopy(result)

    def get_result(self, result_id):
        for result in self.results:
            if result.id == result_id:
                return result
        raise TaskResultDoesNotExist(result_id)
