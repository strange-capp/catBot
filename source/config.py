import os


def get_token():
    return os.environ.get('BOT_URL')


def get_url():
    return os.environ.get('BOT_TOKEN')


BASEDIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

ADMINS = [782633810]
