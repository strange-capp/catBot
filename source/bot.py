from flask import Flask, abort, request
from telebot import TeleBot, types
import requests
import config, decorators, models

app = Flask(__name__)

bot_token = config.get_token()
url = config.get_url()

cats_url = 'https://api.thecatapi.com/v1/images/search'
vote_url = 'https://api.thecatapi.com/v1/votes/?api_key=9c384300-7b15-449e-991a-205654945bce/'

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
@bot.message_handler(commands=['start', 'help'])
def start(message):
    chat_id = message.chat.id

    user = models.get_user(chat_id)
    if user is None:
        models.new_user(message)

    reply_keys = types.ReplyKeyboardMarkup(resize_keyboard=True)
    get_cat = types.KeyboardButton(text='Кота мне!')
    get_help = types.KeyboardButton(text='Помощь')
    how_to_add = types.KeyboardButton('Добавить кота')

    reply_keys.row(get_cat)
    reply_keys.row(get_help, how_to_add)

    bot.send_message(chat_id, 'Просто тыкай на кнопку и наслаждайся🐈)',
                     reply_markup=reply_keys)


@bot.message_handler(func=lambda message: 'Кота мне!' in message.text)
def give_cat(message):
    chat_id = message.chat.id

    user = models.get_user(chat_id)
    if user is None:
        user = models.new_user(message)

    response = requests.get(cats_url).json()[0]
    photo = response['url']
    image_id = response['id']

    vote_markup = types.InlineKeyboardMarkup(row_width=2)

    vote_up_button = types.InlineKeyboardButton(
        '👍',
        callback_data=f'up{image_id}')
    vote_down_button = types.InlineKeyboardButton(
        '👎',
        callback_data=f'down{image_id}')

    vote_markup.add(vote_up_button, vote_down_button)

    bot.send_photo(chat_id=chat_id, photo=photo,
                   reply_markup=vote_markup)

    user.messages = int(user.messages) + 1 if user.messages is not None \
        else 1
    models.session.add(user)
    models.session.commit()


@bot.message_handler(func=lambda message: 'Добавить кота' in message.text)
def add_cat(message):
    chat_id = message.chat.id

    text = "Я уже начал разрабатывать" \
           " ИИ, который будет способен распознать " \
           "кота на твоей фотографии и не дать " \
           "ТЕБЕ отправить вместо кота свой нюдес, " \
           "нужно просто (не)много подождать)"

    bot.send_message(chat_id, text)


@bot.callback_query_handler(func=lambda call: 'up' in call.data)
def vote_up(call):
    chat_id = call.message.chat.id

    image_id = call.data.replace('up', '')

    json = {'image_id': image_id, 'value': 1}

    response = requests.post(vote_url, json=json)
    message = response.json()['message']
    if message == 'SUCCESS':
        bot.send_message(chat_id, 'Твой голос будет учтен!!')


@bot.callback_query_handler(func=lambda call: 'down' in call.data)
def vote_down(call):
    chat_id = call.message.chat.id

    image_id = call.data.replace('down', '')

    json = {'image_id': image_id, 'value': 0}

    response = requests.post(vote_url, json=json)
    message = response.json()['message']
    print(response.json())
    if message == 'SUCCESS':
        bot.send_message(chat_id, 'Твой голос будет учтен..')


@bot.message_handler(commands=['logs'])
@decorators.admin
def logs(message):
    chat_id = message.chat.id

    users = models.get_all_users()

    text = ''
    messages = 0

    for user in users:
        row = f'{user.id}. {user.name}(@{user.username}).\n' \
              f'Всего сообщений от {user.name}- {user.messages}\n'
        text += row
        messages += int(user.messages)

    total_users = f'Всего пользователей: {len(users)}\n'
    total_messages = f'Всего сообщений: {messages}'

    text += total_users + total_messages

    bot.send_message(chat_id, text)


@bot.message_handler(func=lambda message: 'sendToAll' in message.text)
@decorators.admin
def send_to_all(message):
    """
    Sends given message to all users
    """
    text = message.text.replace('/sendToAll ', '')
    users = models.get_all_users()

    for user in users:
        bot.send_message(user.chat_id, text)


bot.polling()
