from aiohttp import web

from webgpio.main import init_app


if __name__ == '__main__':
    app = init_app()
    web.run_app(app)
