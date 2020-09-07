from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Integer, Column, create_engine
from sqlalchemy.orm import sessionmaker

import os

from config import BASEDIR

engine = create_engine('sqlite:///' + os.path.join(BASEDIR, 'data.sqlite'),
                       echo=True, connect_args={'check_same_thread': False})

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    name = Column(String(length=64))
    username = Column(String(length=64))
    phone = Column(String)
    messages = Column(Integer)


def new_user(data):
    chat_id = data.chat.id
    try:
        username = data.chat.username
    except AttributeError:
        username = 'None'

    try:
        name = data.chat.first_name
    except AttributeError:
        name = 'None'

    user = User(chat_id=chat_id, name=name, username=username)
    session.add(user)
    session.commit()
    return User


def get_user(chat_id):
    user = session.query(User).filter_by(chat_id=chat_id)
    return user


def get_all_users():
    users = session.query(User).all()
    return users
