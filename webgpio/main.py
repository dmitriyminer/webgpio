import asyncio
import logging
import pathlib

import aiohttp_jinja2
import aioredis
from aiohttp import web
from aiohttp_session import session_middleware
from aiohttp_session.redis_storage import RedisStorage
from aiopg.sa import create_engine
from jinja2 import FileSystemLoader as JinjaLoader

from .auth.routes import setup_routes as setup_auth_routes
from .device.helpers import timestamp_format
from .device.routes import setup_routes as setup_device_routes
from .middlewares import auth_middleware
from .routes import setup_routes
from .rq import rq_tasks
from .utils import load_config
from .ws.routes import setup_routes as setup_ws_routes

ROOT_PATH = pathlib.Path(__file__).parent
CONFIG_PATH = str(ROOT_PATH / 'config' / 'base.yaml')


def setup_logger(name, filename):
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    fh = logging.FileHandler(filename)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(log_format))
    logger.addHandler(fh)


def init_app():
    conf = load_config(CONFIG_PATH)
    setup_logger('auth.logger', 'auth.log')
    setup_logger('device.logger', 'device.log')
    setup_logger('ws.logger', 'ws.log')

    # init redis pool first, need for RedisStorage in session_middleware
    loop = asyncio.get_event_loop()
    redis_pool = loop.run_until_complete(init_redis(conf))

    app = web.Application(loop=loop)

    app.middlewares.append(
        session_middleware(RedisStorage(redis_pool=redis_pool,
                                        max_age=30 * 24 * 3600))
    )
    app.middlewares.append(auth_middleware)

    env = aiohttp_jinja2.setup(
        app,
        context_processors=(aiohttp_jinja2.request_processor,),
        loader=JinjaLoader(str(ROOT_PATH / 'templates')))

    # add aiohttp_jinja2 filter
    env.filters['timestamp_format'] = timestamp_format

    app['redis'] = redis_pool
    app['config'] = conf
    app['sockets'] = []
    setup_routes(app)
    setup_auth_routes(app)
    setup_device_routes(app)
    setup_ws_routes(app)

    app.on_startup.append(init_pg)
    app.on_startup.append(rq_tasks)
    app.on_cleanup.append(close_pg)
    app.on_cleanup.append(close_redis)
    app.on_shutdown.append(close_sockets)

    if app['config']['DEBUG']:
        import aiohttp_debugtoolbar
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)

    return app


async def init_pg(app):
    conf = app['config']
    engine = await create_engine(database=conf['database'],
                                 user=conf['user'],
                                 password=conf['password'],
                                 host=conf['host'],
                                 port=conf['port'],
                                 loop=app.loop)
    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()


async def init_redis(conf):
    pool = await aioredis.create_pool((conf['redis_host'],
                                       conf['redis_port']))
    return pool


async def close_redis(app):
    app['redis'].close()
    await app['redis'].wait_closed()


async def close_sockets(app):
    for ws in app['sockets']:
        await ws.close()
