import logging

import aiohttp
from aiohttp import web

auth_logger = logging.getLogger('ws.logger')


async def gpio_status(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    # TODO ADD AUTH
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                auth_logger.info('%s %s' %
                                 (msg.data,
                                  request.cookies.get('AIOHTTP_SESSION')))
                ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            auth_logger.info('ws connection closed with '
                             'exception %s' % ws.exception())

    auth_logger.info('websocket connection closed')
    return ws
