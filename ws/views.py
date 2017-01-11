import logging

import aiohttp
from aiohttp import web

from device.sa import check_device_permissions, sa_port_status
from device.utils import device_status_update

auth_logger = logging.getLogger('ws.logger')


async def gpio_status(request):
    device = request.match_info['device']
    permit = await check_device_permissions(request.app['db'],
                                            request.user,
                                            device)
    if permit is None:
        return web.HTTPForbidden(body=b'Permission denied')

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            elif msg.data == 'status':
                auth_logger.info('%s %s' %
                                 (msg.data,
                                  request.cookies.get('AIOHTTP_SESSION')))
                resp = await sa_port_status(request.app['db'], device)
                ws.send_str(resp)
                await device_status_update(request.app['redis'], device)

        elif msg.type == aiohttp.WSMsgType.ERROR:
            auth_logger.info('ws connection closed with '
                             'exception %s' % ws.exception())

    auth_logger.info('websocket connection closed')
    return ws
