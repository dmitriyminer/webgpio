import uuid


def generate_key():
    return uuid.uuid4().hex.upper()[:8]
