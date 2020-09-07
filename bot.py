from flask import Flask, abort, request
from telebot import TeleBot, types
import config
import models
import requests

app = Flask(__name__)

bot_token = config.get_token()
url = config.get_url()

cats = 'https://api.thecatapi.com/v1/images/search'

bot = TeleBot(bot_token)


@app.route('/{}'.format(bot_token), methods=['POST'])
def index():
    if request.method == "POST":
        json_string = request.data.decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'Works'
    else:
        return abort(403)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook('{}/{}'.format(url, bot_token), )
    if s:
        print(s)
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@bot.message_handler(func=lambda message: 'Помощь' in message.text)
@bot.message_handler(commands=['start, help'])
def start(message):
    chat_id = message.chat_id

    user = models.get_user(chat_id)
    if user is None:
        user = models.new_user(message)

    reply_keys = types.ReplyKeyboardMarkup(resize_keyboard=True)
    get_cat = types.KeyboardButton(text='Кота мне')
    get_help = types.KeyboardButton(text='Помощь')
    how_to_add = types.KeyboardButton('Добавить кота')

    reply_keys.row(get_cat)
    reply_keys.row(get_help, how_to_add)

    bot.send_message(chat_id, 'Просто тыкай на кнопку и наслаждайся🐈)',
                     reply_markup=reply_keys)


@bot.message_handler(func=lambda message: 'Кота мне' in message.text)
def give_cat(message):
    chat_id = message.chat_id

    user = models.get_user(chat_id)
    if user is None:
        user = models.new_user(message)

    photo = requests.get(cats).json()['url']

    bot.send_photo(chat_id=chat_id, photo=photo)

    user.messages += 1
    models.session.add(user)
    models.session.commit()


@bot.message_handler(func=lambda message: 'Добавить кота' in message.text)
def add_cat(message):
    chat_id = message.chat.id

    text = """
Я уже начал разрабатывать ИИ,
который будет способен распознать кота на твоей фотографии
и не дать ТЕБЕ отправить вместо кота свой нюдес,
нужно просто (не)много подождать)"""

    bot.send_message(chat_id, text)


@bot.message_handler(commands=['logs'])
def logs(message):
    chat_id = message.chat.id

    if chat_id not in config.ADMINS:
        return

    users = models.get_all_users()

    text = ''

    for user in users:
        row = f'{user.id}. {user.name}(@{user.username}).\n' \
              f'Всего сообщений - {user.messages}\n'
        text += row

    bot.send_message(chat_id, text)
