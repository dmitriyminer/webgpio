import json
import logging
import time

import sqlalchemy as sa

from db import devices, ports
from device.redis import gather_redis_tasks
from device.utils import generate_key, RedisInfoTask

NUM_GPIO = 28
STATUS_TIME = 60
device_logger = logging.getLogger('device.logger')


async def check_device_permissions(db, user, device):
    async with db.acquire() as conn:
        query = sa.select([devices]).where(
            sa.and_(devices.c.key == device,
                    devices.c.user_id == user))
        ret = await conn.execute(query)
        obj = await ret.fetchone()
        if obj is not None:
            return obj.id
        else:
            device_logger.info(f'User ID: {user} has no permissions'
                               f'to device: {device}')


async def sa_port_update(db, user, device, statuses):
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        async with db.acquire() as conn:
            for status in statuses:
                stmt = sa.update(ports).where(
                    sa.and_(ports.c.gpio == status['gpio'],
                            devices.c.id == device_id)) \
                    .values(status=status['status'])
                await conn.execute(stmt)
            device_logger.info(f'Port update statuses:{statuses}')


async def sa_port_add(db, user, device, **kwargs):
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        async with db.acquire() as conn:
            await conn.scalar(
                ports.insert().values(device_id=device_id,
                                      gpio=kwargs.get('gpio'),
                                      name=kwargs.get('name'),
                                      status=kwargs.get('status') == 'on'))
            gpio = kwargs.get('gpio')
            name = kwargs.get('name')
            status = 'on' if kwargs.get('status') else 'off'
            device_logger.info(f'Port add name:{name} key:{device} '
                               f'id:{gpio} status:{status}')


async def sa_port_delete(db, user, device, port):
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        async with db.acquire() as conn:
            stmt = sa.delete(ports).where(
                sa.and_(ports.c.id == port,
                        ports.c.device_id == device_id))
            await conn.execute(stmt)
            device_logger.info(f'Port delete key:{device} id:{port}')


async def sa_port(db, user, device, port):
    obj = None
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        async with db.acquire() as conn:
            stmt = sa.select([ports]).where(
                sa.and_(ports.c.id == port, ports.c.device_id == device_id))
            ret = await conn.execute(stmt)
            obj = await ret.fetchone()

    return obj


async def sa_port_edit(db, user, **kwargs):
    device_id = await check_device_permissions(db, user, kwargs.get('device'))
    if device_id is not None:
        async with db.acquire() as conn:
            stmt = sa.update(ports).where(
                sa.and_(ports.c.id == kwargs.get('port'),
                        devices.c.id == device_id)) \
                .values(gpio=kwargs.get('gpio'),
                        name=kwargs.get('name'),
                        status=kwargs.get('status') == 'on')
            await conn.execute(stmt)


async def sa_device_add(db, user, **kwargs):
    async with db.acquire() as conn:
        key = generate_key()
        while True:
            ret = await conn.execute(
                devices.select().where(devices.c.key == key))
            obj = await ret.fetchone()
            if obj is not None:
                key = generate_key()
            else:
                break
        await conn.scalar(
            devices.insert().values(name=kwargs.get('name'),
                                    user_id=user,
                                    key=key))


async def sa_device_delete(db, user, device):
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        async with db.acquire() as conn:
            stmt = sa.delete(devices).where(
                sa.and_(devices.c.key == device, devices.c.user_id == user))
            await conn.execute(stmt)
            device_logger.info(f'Device delete key:{device}')


async def sa_port_list(db, user, device):
    objs = []
    device_id = await check_device_permissions(db, user, device)
    if device_id is not None:
        j = sa.join(devices, ports, devices.c.id == ports.c.device_id)
        stmt = sa.select([ports]).select_from(j)\
            .where(devices.c.key == device).order_by(ports.c.gpio)
        async with db.acquire() as conn:
            async for row in conn.execute(stmt):
                objs.append(row)
    return objs


async def sa_port_status(db, device):
    """
    Return: ports status for specific device
    '[{'gpio': 1, 'status': True}, {'gpio': 2, 'status': True}]'

    """
    ports_status = []
    j = sa.join(devices, ports, devices.c.id == ports.c.device_id)
    stmt = sa.select([ports]).select_from(j) \
        .where(devices.c.key == device).order_by(ports.c.gpio)
    async with db.acquire() as conn:
        async for row in conn.execute(stmt):
            ports_status.append({'gpio': row.gpio, 'status': row.status})

    return json.dumps(ports_status)


async def sa_device_list(db, user):
    objs = []
    query = sa.select([devices]).where(devices.c.user_id == user)\
        .order_by(devices.c.id)
    async with db.acquire() as conn:
        async for row in conn.execute(query):
            objs.append(row)
    return objs


async def sa_device_status(redis, objs, user):
    status = dict()
    async with redis.get() as conn:
        for obj in objs:
            key = obj.key
            value = await conn.get(f'STATUS_{key}')
            if value:
                status[key] = time.time() - float(value) < STATUS_TIME
    return status


async def sa_free_gpio(db, user, device):
    all_ports = range(1, NUM_GPIO+1)
    used_ports = []
    query = sa.select([devices]).where(
        sa.and_(devices.c.key == device, devices.c.user_id == user))
    async with db.acquire() as conn:
        ret = await conn.execute(query)
        obj = await ret.fetchone()
        if obj is not None:
            query = ports.select().where(ports.c.device_id == obj.id)
            async for row in conn.execute(query):
                used_ports.append(row.gpio)
    return [port for port in all_ports if port not in used_ports]


async def sa_device_gpio(db, user, device):
    used_ports = []
    query = sa.select([devices]).where(
        sa.and_(devices.c.key == device, devices.c.user_id == user))
    async with db.acquire() as conn:
        ret = await conn.execute(query)
        obj = await ret.fetchone()
        if obj is not None:
            query = ports.select().where(ports.c.device_id == obj.id)\
                .order_by(ports.c.gpio)
            async for row in conn.execute(query):
                used_ports.append(row.gpio)
    return used_ports


async def user_tasks(redis, db, user):
    tasks = await gather_redis_tasks(redis, user)
    rows = []
    async for task in RedisInfoTask(tasks):
        j = sa.join(devices, ports, devices.c.id == ports.c.device_id)
        async with db.acquire() as conn:
            stmt = sa.select([ports]).select_from(j) \
                .where(sa.and_(devices.c.key == task.device,
                               ports.c.gpio == task.gpio))
            async for row in conn.execute(stmt):
                rows.append({'task': task, 'port': row})
    return rows
