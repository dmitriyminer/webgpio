import os
import pathlib

import trafaret as t
import yaml
from dotenv import load_dotenv

EXAMPLE_SECRET = 'CO8-hNHdHZ8fK-VjZgBf0OWQ-fFSCwP1T-u1cLSPeV8='


def load_config(f):
    env_path = str(pathlib.Path(__file__).parent / '.env')
    load_dotenv(env_path)

    with open(f) as opened:
        data = yaml.safe_load(opened)

    data['SECRET_KEY'] = os.environ.get('SECRET_KEY') or EXAMPLE_SECRET

    t.Bool().check(data.get('DEBUG'))
    t.String().check(data.get('host'))
    t.String().check(data.get('database'))
    t.String().check(data.get('user'))
    t.String().check(data.get('password'))
    t.String().check(data.get('redis_host'))
    t.Int().check(data.get('redis_port'))
    t.String(regex=r'^[0-9a-zA-Z_=\-]{44}$').check(data.get('SECRET_KEY'))
    # generate SECRET_KEY base64.urlsafe_b64encode(os.urandom(32))

    return data
