import uuid

from aiohttp_session import Session
from aiohttp_session.redis_storage import RedisStorage


class CustomRedisStorage(RedisStorage):
    async def load_session(self, request):
        if self._redis is None:
            self._redis = request.app['redis']

        cookie = self.load_cookie(request)
        if cookie is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        else:
            async with self._redis.get() as conn:
                key = str(cookie)
                data = await conn.get(self.cookie_name + '_' + key)
                if data is None:
                    return Session(None, data=None,
                                   new=True, max_age=self.max_age)
                data = data.decode('utf-8')
                data = self._decoder(data)
                return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(self, request, response, session):
        if self._redis is None:
            self._redis = request.app['redis']

        key = session.identity
        if key is None:
            key = uuid.uuid4().hex
            self.save_cookie(response, key,
                             max_age=session.max_age)
        else:
            key = str(key)
            self.save_cookie(response, key,
                             max_age=session.max_age)

        data = self._encoder(self._get_session_data(session))
        async with self._redis.get() as conn:
            max_age = session.max_age
            expire = max_age if max_age is not None else 0
            await conn.set(self.cookie_name + '_' + key,
                           data, expire=expire)
