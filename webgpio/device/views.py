import aiohttp_jinja2
import sqlalchemy as sa
from aiohttp import web

from webgpio.db import devices
from .redis import device_tasks_add
from .sa import (sa_port_update, sa_device_delete, sa_port_delete,
                 sa_port_list, sa_device_list, sa_device_add,
                 sa_port_add, sa_free_gpio, sa_port, sa_port_edit,
                 sa_device_status, user_tasks, sa_device_gpio,
                 check_device_permissions)
from .utils import recurrence_values


@aiohttp_jinja2.template('base.html')
async def home(request):
    context = dict(content='Some content')
    return context


@aiohttp_jinja2.template('device/devices.html')
async def device_list(request):
    objs = await sa_device_list(request.app['db'], request.user)
    status = await sa_device_status(request.app['redis'], objs, request.user)
    context = {'devices': objs,
               'status': status}
    return context


@aiohttp_jinja2.template('device/ports.html')
async def port_list(request):
    device = request.match_info['device']
    ports = await sa_port_list(request.app['db'], request.user, device)
    context = {'ports': ports, 'device': device}
    return context


@aiohttp_jinja2.template('device/port_edit.html')
async def port_edit(request):
    device = request.match_info['device']
    port = request.match_info['port']
    data = await request.post()
    if data.get('name') and data.get('gpio'):
        await sa_port_edit(request.app['db'], request.user,
                           port=port, device=device, **data)
        url = request.app.router['ports'].url(parts={'device': device})
        return web.HTTPFound(url)

    port = await sa_port(request.app['db'], request.user, device, port)
    gpios = await sa_free_gpio(request.app['db'], request.user, device)
    gpios.append(port.gpio)
    gpios.sort()
    context = {'gpios': gpios, 'device': device, 'port': port}
    return context


async def port_update(request):
    device = request.match_info['device']
    data = await request.post()
    filtered = [{key: value}
                for key, value in data.items() if key.startswith('status_')]
    if filtered:
        statuses = []
        for item in data:
            gpio = item.split('_')[1]
            statuses.append({'gpio': gpio, 'status': data[item] == 'on'})
        await sa_port_update(request.app['db'], request.user, device, statuses)

    url = request.app.router['ports'].url(parts={'device': device})
    return web.HTTPFound(url)


@aiohttp_jinja2.template('device/port_add.html')
async def port_add(request):
    device = request.match_info['device']
    context = dict()
    context['gpio'] = await sa_free_gpio(request.app['db'],
                                         request.user,
                                         device)
    data = await request.post()
    valid_gpio = await sa_free_gpio(request.app['db'], request.user, device)

    try:
        gpio = int(data.get('gpio'))
    except Exception:
        gpio = None

    if data and data.get('name') and gpio in valid_gpio:
        await sa_port_add(request.app['db'], request.user, device, **data)
        url = request.app.router['ports'].url(parts={'device': device})
        return web.HTTPFound(url)
    return context


@aiohttp_jinja2.template('device/edit.html')
async def device_edit(request):
    device = request.match_info['device']
    data = await request.post()
    if data.get('name'):
        async with request.app['db'].acquire() as conn:
            stmt = sa.update(devices).where(
                sa.and_(devices.c.key == device,
                        devices.c.user_id == request.user)).\
                values(name=data.get('name'))
            await conn.execute(stmt)
        url = request.app.router['devices'].url()
        return web.HTTPFound(url)
    else:
        context = dict()
        query = sa.select([devices]).where(devices.c.key == device)
        async with request.app['db'].acquire() as conn:
            ret = await conn.execute(query)
            context['obj'] = await ret.fetchone()
        return context


@aiohttp_jinja2.template('device/add.html')
async def device_add(request):
    context = {}
    data = await request.post()
    if data and data.get('name'):
        await sa_device_add(request.app['db'], request.user, **data)
        url = request.app.router['devices'].url()
        return web.HTTPFound(url)
    return context


async def device_delete(request):
    name = request.match_info['device']
    await sa_device_delete(request.app['db'], request.user, name)
    url = request.app.router['devices'].url()
    return web.HTTPFound(url)


async def port_delete(request):
    device = request.match_info['device']
    port = request.match_info['port']
    await sa_port_delete(request.app['db'], request.user, device, port)
    url = request.app.router['port-update'].url(parts={'device': device})
    return web.HTTPFound(url)


@aiohttp_jinja2.template('device/tasks.html')
async def tasks(request):
    context = dict()
    context['active_tasks'] = await user_tasks(request.app['redis'],
                                               request.app['db'],
                                               request.user)
    return context


@aiohttp_jinja2.template('device/task_add.html')
async def task_add(request):
    device = request.match_info['device']
    context = dict()
    device_id = await check_device_permissions(request.app['db'],
                                               request.user,
                                               device)
    if device_id is not None:
        context['gpio'] = await sa_device_gpio(request.app['db'],
                                               request.user,
                                               device)
    if request.method == 'POST':
        data = await request.post()
        if device_id is not None and data:
            await device_tasks_add(request.app['redis'],
                                   request.app['db'],
                                   request.user,
                                   device,
                                   context['gpio'],
                                   **data)
            url = request.app.router['ports'].url(parts={'device': device})
            return web.HTTPFound(url)

    return context


@aiohttp_jinja2.template('device/task_recurrence_add.html')
async def task_recurrence_add(request):
    device = request.match_info['device']
    context = dict()
    device_id = await check_device_permissions(request.app['db'],
                                               request.user,
                                               device)
    if device_id is not None:
        context['gpio'] = await sa_device_gpio(request.app['db'],
                                               request.user,
                                               device)
        if request.method == 'POST':
            data = await request.post()

            await device_tasks_add(request.app['redis'],
                                   request.app['db'],
                                   request.user,
                                   device,
                                   context['gpio'],
                                   date=data['rrules'],
                                   **data)

            url = request.app.router['ports'].url(parts={'device': device})
            return web.HTTPFound(url)

    return context


async def task_recurrence_values(request):
    data = await recurrence_values(request.query_string)

    return web.json_response({'data': data})
