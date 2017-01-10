import uuid

import time


def generate_key():
    return uuid.uuid4().hex.upper()[:8]


async def device_status_update(redis, device):
    async with redis.get() as conn:
        await conn.set(f'STATUS_{device}', time.time())
