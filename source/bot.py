from aiogram import Dispatcher, Bot, types, dispatcher
import requests
import config, models
from urllib.parse import urljoin
import os
from aiogram.utils.executor import start_webhook

bot_token = config.get_token()
url = config.get_url()

WEBHOOK_HOST = f'https://catcatcat-bot.herokuapp.com/'  # Enter here your link from Heroku project settings
WEBHOOK_URL_PATH = '/webhook/' + bot_token
WEBHOOK_URL = urljoin(WEBHOOK_HOST, WEBHOOK_URL_PATH)

cats_url = 'https://api.thecatapi.com/v1/images/search'
vote_url = 'https://api.thecatapi.com/v1/votes/?api_key=9c384300-7b15-449e-991a-205654945bce/'

bot = Bot(bot_token)
dp = Dispatcher(bot)

@dp.message_handler(
    dispatcher.filters.builtin.Text(equals='Помощь')
)
@dp.message_handler(commands=['start', 'help'])
async def start(message):
    """
    Sends a help message
    """
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

    await bot.send_message(chat_id, 'Просто тыкай на кнопку и наслаждайся🐈)',
                           reply_markup=reply_keys)


@dp.message_handler(
    dispatcher.filters.builtin.Text(equals='Кота мне!')
)
async def give_cat(message):
    """
    Sends a cat
    """
    chat_id = message.chat.id

    user = models.get_user(chat_id)
    if user is None:
        user = models.new_user(message)

    response = requests.get(cats_url).json()[0]
    photo = response['url']
    image_id = response['id']

    markup = types.InlineKeyboardMarkup(row_width=2)

    vote_up_button = types.InlineKeyboardButton(
        '👍',
        callback_data=f'up{image_id}')
    vote_down_button = types.InlineKeyboardButton(
        '👎',
        callback_data=f'down{image_id}')

    send_photo = types.InlineKeyboardButton('Отправить всем пользователям!',
                                            callback_data=f'send{photo}')

    markup.row(vote_up_button, vote_down_button)
    markup.add(send_photo)

    await bot.send_photo(chat_id=chat_id, photo=photo,
                         reply_markup=markup)

    user.messages = int(user.messages) + 1 if user.messages is not None \
        else 1
    models.session.add(user)
    models.session.commit()


@dp.message_handler(dispatcher.filters.builtin.Text(
    contains='Добавить кота'))
async def add_cat(message):
    """
    Sends message about current state of 'Add a cat' feature
    """
    chat_id = message.chat.id

    text = "Я уже начал разрабатывать" \
           " ИИ, который будет способен распознать " \
           "кота на твоей фотографии и не дать " \
           "ТЕБЕ отправить вместо кота свой нюдес, " \
           "нужно просто (не)много подождать)"

    await bot.send_message(chat_id, text)


@dp.callback_query_handler(lambda call: 'up' in call.data)
async def vote_up(call):
    """
    Sends vote_up to the thecatapi.com
    """
    chat_id = call.message.chat.id

    image_id = call.data.replace('up', '')

    json = {'image_id': image_id, 'value': 1}

    response = requests.post(vote_url, json=json)
    message = response.json()['message']
    if message == 'SUCCESS':
        await bot.send_message(chat_id, 'Твой голос будет учтен!!')


@dp.callback_query_handler(lambda call: 'down' in call.data)
async def vote_down(call):
    """
    Sends vote_down to the thecatapi.com
    """
    chat_id = call.message.chat.id

    image_id = call.data.replace('down', '')

    json = {'image_id': image_id, 'value': 0}

    response = requests.post(vote_url, json=json)
    message = response.json()['message']
    if message == 'SUCCESS':
        await bot.send_message(chat_id, 'Твой голос будет учтен..')


@dp.callback_query_handler(lambda call: 'send' in call.data)
async def resend_photo(call):
    photo_url = call.data.replace('send', '')

    current_user = models.get_user(call.message.chat.id)
    print(models.get_all_users)
    for i in models.get_all_users():
        if not i.chat_id == current_user.chat_id:
            await bot.send_photo(i.chat_id, photo=photo_url)

    await bot.send_message(current_user.chat_id, 'Фотография отправлена'
                                                 ' всем пользователям!')

# for admins
@dp.message_handler(commands=['logs'])
async def logs(message):
    """
    Sends stats to the admin
    """
    chat_id = message.chat.id

    if chat_id not in config.ADMINS:
        return

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

    await bot.send_message(chat_id, text)


@dp.message_handler(lambda message: 'sendToAll' in message.text)
def send_to_all(message):
    """
    Sends given message to all users
    """
    if message.chat.id not in config.ADMINS:
        return

    text = message.text.replace('/sendToAll ', '')
    users = models.get_all_users()

    for user in users:
        bot.send_message(user.chat_id, text)


async def on_startup(app):
    """
    Simple hook for aiohttp application which manages webhook
    """
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_URL_PATH,
        on_startup=on_startup,
        skip_updates=True,
        host='0.0.0.0',
        port=os.getenv('PORT'),
    )
