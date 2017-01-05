from .views import gpio_status


def setup_routes(app):
    app.router.add_route('*', '/gpio/status', gpio_status, name='gpio_status')
