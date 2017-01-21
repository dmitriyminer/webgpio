import pathlib


def setup_routes(app):
    app.router.add_static('/static/',
                          path=str(pathlib.Path(__file__).parent / 'static'),
                          name='static')
