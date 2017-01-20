import asyncio
import json
from collections import deque
from urllib.parse import urlencode

import RPi.GPIO as GPIO
import aiohttp

REMOTE_PORT = '8080'
REMOTE_SERVER = f'http://127.0.0.1:{REMOTE_PORT}'
LOGIN_URL = f'{REMOTE_SERVER}/login'
EMAIL = 'user@mail.com'
PASSWD = 'password'
DEVICE_KEY = '43E701BF'
DEVICE_URL = f'{REMOTE_SERVER}/ws/{DEVICE_KEY}/status'
UPDATE_TIME = 1
DEQUE_LENGTH = 28

SESSION_KEY = 'AIOHTTP_SESSION'
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

GPIO.setmode(GPIO.BCM)


class WebGPIOClient:
    def __init__(self, loop):
        self._loop = loop
        self._cookie = None
        self._ports_status = deque(maxlen=DEQUE_LENGTH)
        self._current_status = dict()

    async def auth(self):
        data = urlencode({'email': EMAIL, 'passwd': PASSWD})
        async with aiohttp.ClientSession(
                loop=self._loop, headers=HEADERS) as client:
            async with client.post(LOGIN_URL, data=data) as resp:
                history = next(iter(resp.history), None)
                if history:
                    cookies = history.cookies.get(SESSION_KEY)
                    self._cookie = (cookies.key, cookies.value)
        return self._cookie

    async def client(self):
        _, cookie = await self.auth()
        if self._cookie is not None:
            async with aiohttp.ClientSession(
                    loop=self._loop, cookies={SESSION_KEY: cookie}) as session:
                async with session.ws_connect(DEVICE_URL) as ws:
                    while True:
                        ws.send_str('status')
                        await asyncio.sleep(UPDATE_TIME)
                        msg = await ws.receive()
                        try:
                            ports_status = json.loads(msg.data)
                        except Exception:
                            ports_status = []
                        self._ports_status.extend(ports_status)

    async def controller(self):
        while True:
            try:
                item = self._ports_status.popleft()
            except IndexError:
                await asyncio.sleep(UPDATE_TIME)
            else:
                gpio = item.get('gpio')
                status = item.get('status')

                if gpio not in self._current_status:
                    GPIO.setup(gpio, GPIO.OUT)

                if self._current_status.get(gpio) != status:
                    self._current_status[gpio] = status
                    GPIO.output(gpio, status)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        ws = WebGPIOClient(loop)
        tasks = [asyncio.ensure_future(ws.client()),
                 asyncio.ensure_future(ws.controller())]
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        GPIO.cleanup()
