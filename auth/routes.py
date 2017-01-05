from .views import login, register, logout


def setup_routes(app):
    app.router.add_route('*', '/login', login, name='login')
    app.router.add_route('*', '/register', register, name='register')
    app.router.add_get('/logout', logout, name='logout')
