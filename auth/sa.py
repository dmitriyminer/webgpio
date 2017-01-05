import crypt
from hmac import compare_digest

from db import users


async def check_password(db, config, **kwargs):
    async with db.acquire() as conn:
        stmt = users.select().where(users.c.email == kwargs.get('email'))
        ret = await conn.execute(stmt)
        obj = await ret.fetchone()

        hashed = crypt.crypt(kwargs.get('passwd'), salt=config['SECRET_KEY'])
        if obj is not None and compare_digest(obj.passwd, hashed):
            return obj.id


async def user_exist(db, **kwargs):
    async with db.acquire() as conn:
        stmt = users.select().where(users.c.email == kwargs.get('email'))
        ret = await conn.execute(stmt)
        obj = await ret.fetchone()

        return obj is not None


async def create_user(db, config, **kwargs):
    hashed = crypt.crypt(kwargs.get('passwd'), salt=config['SECRET_KEY'])
    async with db.acquire() as conn:
        await conn.scalar(
            users.insert().values(name=kwargs.get('username'),
                                  email=kwargs.get('email'),
                                  passwd=hashed))

        stmt = users.select().where(users.c.email == kwargs.get('email'))
        ret = await conn.execute(stmt)
        obj = await ret.fetchone()

        if obj is not None:
            return obj.id
