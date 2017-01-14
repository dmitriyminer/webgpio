import time
import uuid
from collections import namedtuple, deque

REDIS_USER_TASK_KEY = f'user:{user}:tasks'

TaskInfo = namedtuple('TaskInfo', ['timestamp', 'device', 'gpio', 'action'])


def generate_key():
    return uuid.uuid4().hex.upper()[:8]


async def device_status_update(redis, device):
    async with redis.get() as conn:
        await conn.set(f'STATUS_{device}', time.time())


async def gather_redis_tasks(redis, user):
    async with redis.get() as conn:
        return await conn.zrangebyscore(REDIS_USER_TASK_KEY, 0, float('+inf'))


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
