from .views import (home, device_list, port_list, port_update, device_edit,
                    device_delete, port_delete, device_add, port_add,
                    port_edit, tasks, task_add, task_recurrence_add,
                    task_recurrence_values, task_delete)


def setup_routes(app):
    app.router.add_get('/', home, name='home')
    app.router.add_get('/devices', device_list, name='devices')
    app.router.add_get('/tasks', tasks, name='tasks'),
    app.router.add_get('/device/{device}/port/{port}/delete',
                       port_delete, name='port-delete')
    app.router.add_route('*', '/device/add', device_add, name='device-add')
    app.router.add_route('*', '/device/{device}/port/add',
                         port_add, name='port-add')
    app.router.add_route('*', '/device/{device}', port_list, name='ports')
    app.router.add_route('*', '/device/{device}/update',
                         port_update, name='port-update')
    app.router.add_route('*', '/device/{device}/edit',
                         device_edit, name='device-edit')
    app.router.add_route('*', '/device/{device}/delete',
                         device_delete, name='device-delete')
    app.router.add_route('*', '/device/{device}/port/{port}/edit',
                         port_edit, name='port-edit')
    app.router.add_route('*', '/device/{device}/task/add',
                         task_add, name='task-add')
    app.router.add_route('*', '/device/{device}/task/recurrence/add',
                         task_recurrence_add, name='task-recurrence-add')
    app.router.add_get('/api/recurrence/values',
                       task_recurrence_values, name='api-recurrence-values')
    app.router.add_route('POST', '/api/task/delete',
                         task_delete, name='api-task-delete')
