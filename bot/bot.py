import telebot
from config import TOKEN

telebot.apihelper.proxy = {'https': 'socks5h://207.246.82.162:1081'}
bot = telebot.TeleBot(TOKEN)
new_place = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text='Приветствую, ' + message.from_user.first_name)


@bot.message_handler(commands=['add'], content_types=['text'])
def add_place_handler(message):
    msg = bot.reply_to(message, text='Давайте добавим информацию о новом месте. Сначала введите адрес')
    bot.register_next_step_handler(msg, add_place_address)


@bot.message_handler(content_types=['text'])
def add_place_address(message):
    try:
        if message.text is None:
            msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, введите адрес текстом')
            bot.register_next_step_handler(msg, add_place_address)
            return

        new_place['address'] = message.text
        msg = bot.send_message(chat_id=message.chat.id, text='Отлично! Теперь загрузите фото...')
        bot.register_next_step_handler(msg, add_place_photo)

    except Exception:
        msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Попробуйте снова...')
        bot.register_next_step_handler(msg, add_place_address)
        return


@bot.message_handler(content_types=['photo'])
def add_place_photo(message):
    try:
        if message.photo is None:
            msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, загрузите фото')
            bot.register_next_step_handler(msg, add_place_photo)
            return

        new_place['photo'] = message.photo[1]
        new_place['file_id'] = message.photo[1].file_id

        msg = bot.send_message(chat_id=message.chat.id, text='Здорово! Теперь добавьте локацию...')
        bot.register_next_step_handler(msg, add_place_location)

    except Exception:
        msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, загрузите фото')
        bot.register_next_step_handler(msg, add_place_photo)
        return


@bot.message_handler(content_types=['location'])
def add_place_location(message):
    try:
        if message.location is None:
            msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, прикрепите локацию')
            bot.register_next_step_handler(msg, add_place_location)
            return

        new_place['location'] = message.location
        bot.send_message(chat_id=message.chat.id, text='Сохранено')
        print(new_place)
    except Exception:
        msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, прикрепите локацию')
        bot.register_next_step_handler(msg, add_place_location)
        return


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
#bot.polling(none_stop=True, timeout=300)
bot.infinity_polling(True)
