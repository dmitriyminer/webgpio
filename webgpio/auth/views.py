import logging

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from .sa import check_password, user_exist, create_user

auth_logger = logging.getLogger('auth.logger')


@aiohttp_jinja2.template('auth/login.html')
async def login(request):
    session = await get_session(request)
    data = await request.post()
    context = {}

    if data and data.get('email') and data.get('passwd'):
        db = request.app['db']
        config = request.app['config']
        user_id = await check_password(db, config, **data)
        if user_id:
            session['user_id'] = user_id
            auth_logger.info('Login user: %s' % data.get('email'))
            url = request.app.router['devices'].url()
            return web.HTTPFound(url)
        else:
            auth_logger.info('Login error: %s' % data.get('email'))
            context['errors'] = ['Wrong email or password']
    return context


@aiohttp_jinja2.template('auth/register.html')
async def register(request):
    data = await request.post()
    context = dict()
    if all([data, data.get('email'), data.get('passwd'),
            data.get('passwd') == data.get('passwd1')]):
        already_exist = await user_exist(request.app['db'], **data)
        if already_exist:
            context['errors'] = ['User with this email already exists']
            context['username'] = data.get('username', '')
            context['email'] = data.get('email')
        else:
            session = await get_session(request)
            user_id = await create_user(request.app['db'],
                                        request.app['config'], **data)
            session['user_id'] = user_id
            auth_logger.info('Register user: %s' % data.get('email'))
            url = request.app.router['devices'].url()
            return web.HTTPFound(url)
    return context


async def logout(request):
    session = await get_session(request)
    session.pop('user_id', None)
    url = request.app.router['home'].url()
    return web.HTTPFound(url)
