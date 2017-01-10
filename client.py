from urllib.parse import urlencode

import aiohttp
import asyncio

LOGIN_URL = 'http://127.0.0.1:8080/login'
EMAIL = 'user@mail.com'
PASSWD = 'password'
DEVICE_KEY = '43E701BF'
DEVICE_URL = f'http://127.0.0.1:8080/ws/{DEVICE_KEY}/status'

SESSION_KEY = 'AIOHTTP_SESSION'
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


class WebGPIOClient:
    def __init__(self, loop):
        self._loop = loop
        self._cookie = None

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
                        await asyncio.sleep(3)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        ws = WebGPIOClient(loop)
        loop.run_until_complete(ws.client())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
