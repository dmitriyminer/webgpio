import asyncio
import json
from urllib.parse import urlencode

import aiohttp

LOGIN_URL = 'http://127.0.0.1:8080/login'
EMAIL = 'user@mail.com'
PASSWD = 'password'
DEVICE_KEY = '43E701BF'
DEVICE_URL = f'http://127.0.0.1:8080/ws/{DEVICE_KEY}/status'
UPDATE_TIME = 3

SESSION_KEY = 'AIOHTTP_SESSION'
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


class WebGPIOClient:
    def __init__(self, loop):
        self._loop = loop
        self._cookie = None
        self._ports_status = []

    async def auth(self):
        data = urlencode({'email': EMAIL, 'passwd': PASSWD})
        async with aiohttp.ClientSession(
                loop=self._loop, headers=HEADERS) as client:
            async with client.post(LOGIN_URL, data=data) as resp:
                history = next(iter(resp.history), None)
                if history:
                    cookies = history.cookies.get(SESSION_KEY)
                    print(cookies.key, cookies.value)
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
                            self._ports_status = json.loads(msg.data)
                        except Exception:
                            self._ports_status = []
                        print(self._ports_status)

    async def controller(self):
        while True:
            print('controller', self._ports_status)
            await asyncio.sleep(UPDATE_TIME)

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
