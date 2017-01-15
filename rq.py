import asyncio
import time

import sqlalchemy as sa

from db import users, ports, devices
from device.redis import REDIS_USER_TASK_KEY
from device.utils import TaskInfo

RQ_UPDATE_TIME = 1


async def rq_port_update(db, task):
    async with db.acquire() as conn:
        upd = ports.update() \
            .values(status=task.action == 'on') \
            .where(sa.and_(devices.c.id == ports.c.device_id,
                           ports.c.gpio == task.gpio))
        return await conn.execute(upd)


async def rq_executor(db, redis, user_id):
    task_key = REDIS_USER_TASK_KEY.format(user=user_id)
    data = None
    while True:
        async with redis.get() as conn:
            ret = await conn.zrange(task_key, 0, 0)
            data = next(iter(ret), None)

        if data is not None:
            splited = data.decode('utf-8').split(':')
            task = TaskInfo(*splited)

            if float(task.timestamp) <= time.time():
                await rq_port_update(db, task)
                await conn.zrem(task_key, data)
            else:
                await asyncio.sleep(RQ_UPDATE_TIME)

        else:
            await asyncio.sleep(RQ_UPDATE_TIME)


async def rq_tasks(app):
    redis = app['redis']
    db = app['db']
    async with db.acquire() as conn:
        query = sa.select([users])
        async for row in conn.execute(query):
            asyncio.ensure_future(rq_executor(db, redis, row.id))
