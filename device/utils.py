import uuid
from collections import namedtuple, deque

TaskInfo = namedtuple('TaskInfo', ['timestamp', 'device', 'gpio', 'action'])


def generate_key():
    return uuid.uuid4().hex.upper()[:8]


class RedisInfoTask:
    def __init__(self, tasks):
        self._tasks = deque(tasks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            fetched = self._tasks.popleft()
        except IndexError:
            raise StopAsyncIteration

        task = fetched.decode('utf-8').split(':')
        return TaskInfo(*task)
