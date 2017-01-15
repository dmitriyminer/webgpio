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


async def device_task_add(redis, db, user, device, gpio_ports=None, **kwargs):
    created = False
    gpio_ports = gpio_ports or []

    try:
        gpio = int(kwargs.get('gpio'))
        assert gpio in gpio_ports
    except ValueError:
        pass
    except AssertionError:
        pass
    else:
        key = REDIS_USER_TASK_KEY.format(user=user)
        timestamp = datetime.strptime(kwargs.get('date'),
                                      '%Y-%m-%d %H:%M:%S').timestamp()
        value = REDIS_DEVICE_TASK_VALUE.format(timestamp=timestamp,
                                               device=device,
                                               gpio=gpio,
                                               action=kwargs.get('action'))
        if kwargs.get('action') in REDIS_TASK_ACTIONS:
            async with redis.get() as conn:
                created = await conn.zadd(key, timestamp, value)
    return created
