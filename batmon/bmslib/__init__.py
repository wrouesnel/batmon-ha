import asyncio
from typing import Dict, Union, Tuple

# NameType = Union[str, Tuple[str]]
NameType = Union[str, int, Tuple[Union[str, int]]]


class FuturesPool:
    """
    Manage a collection of named futures.
    """
    def __init__(self):
        self._futures: Dict[str, asyncio.Future] = {}

    def acquire(self, name: NameType):
        if isinstance(name, tuple):
            tuple(self.acquire(n) for n in name)
            return FutureContext(name, pool=self)

        assert name not in self._futures, "already waiting for %s" % name
        fut = asyncio.Future()
        self._futures[name] = fut
        return FutureContext(name, pool=self)

    def set_result(self, name, value):
        fut = self._futures.get(name, None)
        if fut:
            if fut.done():
                # silently remove done future 
                self.remove(name)
            else:
                fut.set_result(value)

    def clear(self):
        for fut in self._futures.values():
            fut.cancel()
        self._futures.clear()

    def remove(self, name):
        if isinstance(name, tuple):
            return tuple(self.remove(n) for n in name)
        self._futures.pop(name, None)

    async def wait_for(self, name: NameType, timeout):
        if isinstance(name, tuple):
            tasks = [self.wait_for(n, timeout) for n in name]
            return await asyncio.gather(*tasks, return_exceptions=False)

        try:
            return await asyncio.wait_for(self._futures.get(name), timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            raise
        finally:
            self.remove(name)


class FutureContext:
    def __init__(self, name: NameType, pool: FuturesPool):
        self.name = name
        self.pool = pool

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.remove(self.name)
