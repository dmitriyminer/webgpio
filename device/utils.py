import json
import uuid
from collections import namedtuple, deque
from datetime import datetime
from urllib import parse

from dateutil import rrule

TaskInfo = namedtuple('TaskInfo', ['timestamp', 'device', 'gpio', 'action'])
MAX_RRULE_COUNT = 100


def generate_key():
    return uuid.uuid4().hex.upper()[:8]


class RedisInfoTask:
    def __init__(self, tasks):
        self._tasks = deque(tasks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            fetched = self._tasks.popleft()
        except IndexError:
            raise StopAsyncIteration

        task = fetched.decode('utf-8').split(':')
        return TaskInfo(*task)


async def recurrence_values(query_string):
    data = parse.parse_qs(query_string)
    start_date = next(iter(data.get('start_date', [])), None)
    end_date = next(iter(data.get('end_date', [])), None)
    freq = next(iter(data.get('freq', [])), None)
    count = next(iter(data.get('count', [])), None)
    interval = next(iter(data.get('interval', [])), None)
    weekday = data.get('weekday', [])
    month = data.get('month', [])

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

    if str(count).isdigit():
        count = int(count or 1)
        count = MAX_RRULE_COUNT if count > MAX_RRULE_COUNT else count
    else:
        count = 1

    if str(interval).isdigit():
        interval = int(interval or 1)
    else:
        interval = 1

    freq_map = {'yearly': rrule.YEARLY,
                'monthly': rrule.MONTHLY,
                'weekly': rrule.WEEKLY,
                'daily': rrule.DAILY,
                'hourly': rrule.HOURLY,
                'minutely': rrule.MINUTELY}

    weekday_map = {'monday': rrule.MO,
                   'tuesday': rrule.TU,
                   'wednesday': rrule.WE,
                   'thursday': rrule.TH,
                   'friday': rrule.FR,
                   'saturday': rrule.SA,
                   'sunday': rrule.SU}

    month_map = dict(zip(['january', 'february', 'march', 'april', 'may',
                          'june', 'july', 'august', 'september', 'october',
                          'november', 'december'], range(1, 13)))

    bymonth = [month_map.get(m) for m in month]
    byweekday = [weekday_map.get(d) for d in weekday]

    values = rrule.rrule(freq=freq_map.get(freq, rrule.YEARLY),
                         dtstart=start_date,
                         until=end_date,
                         count=count,
                         bymonth=bymonth,
                         byweekday=byweekday,
                         interval=interval)
    result = [obj.isoformat() for obj in values]

    return json.dumps(result)
