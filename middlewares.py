import json
from aiohttp import web
from aiohttp_session import get_session


async def auth_middleware(app, handler):
    async def middleware(request):
        if any([request.path.startswith(path)
                for path in ('/login', '/register', '/static')]):
            return await handler(request)

        session = await get_session(request)
        auth_cookie = request.cookies.get('AIOHTTP_SESSION')
        async with app['redis'].get() as conn:
            value = await conn.get(f'AIOHTTP_SESSION_{auth_cookie}')

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
