import time
from datetime import datetime

REDIS_DEVICE_STATUS_KEY = 'STATUS_{device}'
REDIS_USER_TASK_KEY = 'USER:{user}:TASKS'
REDIS_DEVICE_TASK_VALUE = '{timestamp}:{device}:{gpio}:{action}'
REDIS_TASK_ACTIONS = ('on', 'off')


async def device_status_update(redis, device):
    async with redis.get() as conn:
        await conn.set(REDIS_DEVICE_STATUS_KEY.format(device=device),
                       time.time())


async def gather_redis_tasks(redis, user):
    async with redis.get() as conn:
        return await conn.zrangebyscore(
            REDIS_USER_TASK_KEY.format(user=user), 0, float('+inf'))


async def device_tasks_add(redis, db, user, device, gpios=None, **kwargs):
    gpios = gpios or []
    action = kwargs.get('action')

    try:
        gpio = int(kwargs.get('gpio'))
    except (TypeError, ValueError):
        gpio = 0

    if gpio in gpios and action in REDIS_TASK_ACTIONS:
        dt_stamps = kwargs.get('date', '').split(',')

        # try to validate timestamps
        try:
            timestamps = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
                          for date in dt_stamps]
        except ValueError:
            timestamps = []

        key = REDIS_USER_TASK_KEY.format(user=user)
        async with redis.get() as conn:
            for timestamp in timestamps:
                tm_stamp = timestamp.timestamp()
                value = REDIS_DEVICE_TASK_VALUE.format(timestamp=tm_stamp,
                                                       device=device,
                                                       gpio=gpio,
                                                       action=action)
                await conn.zadd(key, tm_stamp, value)
