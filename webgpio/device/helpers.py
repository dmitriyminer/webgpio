from datetime import datetime


def timestamp_format(value, dt_format='%Y-%m-%d %H:%M:%S'):
    return datetime.fromtimestamp(float(value)).strftime(dt_format)
