import trafaret as t
import yaml


def load_config(f):
    with open(f) as opened:
        data = yaml.load(opened)

    t.Bool().check(data.get('DEBUG'))
    t.String().check(data.get('host'))
    t.String().check(data.get('database'))
    t.String().check(data.get('user'))
    t.String().check(data.get('password'))
    t.String(regex=r'^[0-9a-zA-Z_=\-]{44}$').check(data.get('SECRET_KEY'))
    # generate SECRET_KEY base64.urlsafe_b64encode(os.urandom(32))

    return data
