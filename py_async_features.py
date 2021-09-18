import asyncio
from typing import Callable, Awaitable

from collections import UserDict
from typing import Any


class AwaitDict(UserDict):
    """Dictionary for asynchronous access fro data"""
    def __init__(self, dict=None, **kwargs):
        self._await_task: dict[str, asyncio.Future] = {}
        super().__init__(dict=None, **kwargs)

    def __setitem__(self, key: str, item: Any):
        future = self._await_task.get(key)
        if future:
            if future.done():
                raise Exception('Expected value has not been received yet')
            future.set_result(item)

        super().__setitem__(key, item)

    def __getitem__(self, item: str) -> Any:
        if item in self._await_task:
            self._await_task.pop(item)

        return super().__getitem__(item)

    async def await_elem(self, key: str) -> Any:
        if key in self._await_task:
            future = self._await_task[key]
        else:
            future = asyncio.Future()
            self._await_task[key] = future
        await future
        return future.result()


def task_error_handler(cb: Callable) -> Callable:
    """Decorator for handling errors occurred in async function. Callback cb is called upon exceptions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                result = await cb(exc)
            return result
        return wrapper
    return decorator


def create_interval(a_func: Callable[..., Awaitable[None]], ms: int) -> asyncio.Task:
    """Periodically execute async function a_func"""
    async def inner():
        while True:
            await asyncio.sleep(ms/1000)
            await asyncio.create_task(a_func())
    return asyncio.create_task(inner())


def create_timer(func: Callable, ms: int) -> asyncio.Task:
    """Execute func after ms milliseconds"""
    async def inner():
        await asyncio.sleep(ms/1000)
        if asyncio.iscoroutinefunction(func):
            await asyncio.create_task(func())
        else:
            func()
    return asyncio.create_task(inner())
