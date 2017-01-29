import json

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from webgpio.constants import AIOHTTP_SESSION


@aiohttp_jinja2.template('error/404.html')
async def handler_404(request):
    return {}


@aiohttp_jinja2.template('error/500.html')
async def handler_500(request):
    return {}


async def auth_middleware(app, handler):

    async def middleware(request):
        if any([request.path.startswith(path)
                for path in ('/login', '/register', '/static')]):
            return await handler(request)

        session = await get_session(request)
        auth_cookie = request.cookies.get(AIOHTTP_SESSION)
        async with app['redis'].get() as conn:
            value = await conn.get(f'{AIOHTTP_SESSION}_{auth_cookie}')

            try:
                data = json.loads(value)
                redis_user = data['session']['user_id']
            except Exception:
                redis_user = None

        session_user = session.get('user_id')
        if session_user and session_user == redis_user:
            request.user = redis_user
            return await handler(request)

        url = request.app.router['login'].url()
        return web.HTTPFound(url)

    return middleware


async def error_middleware(app, handler):

    async def middleware(request):
        try:
            response = await handler(request)

        except web.HTTPException as ex:
            if ex.status == 404:
                return await handler_404(request)

            if app['config']['DEBUG']:
                raise ex

            return await handler_500(request)

        except Exception as ex:
            if app['config']['DEBUG']:
                raise ex

            return await handler_500(request)

        else:
            return response

    return middleware
