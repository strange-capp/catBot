from config import ADMINS


def admin(func):
    def wrapped(*args):
        if args[0].chat.id in ADMINS:
            func(*args)

    return wrapped
