import telebot
from db import users_collection
from datetime import datetime
from operator import itemgetter
from geopy import distance
from config import TOKEN

#telebot.apihelper.proxy = {'https': 'socks5h://51.158.186.141:1080'}
bot = telebot.TeleBot(TOKEN)
new_place = {}


def add_user(message):
    if not users_collection.find_one({'user_id': message.from_user.id}):
        new_user = dict()
        new_user['chat_id'] = message.chat.id
        new_user['user_id'] = message.from_user.id
        new_user['first_name'] = message.chat.first_name
        new_user['last_name'] = message.chat.last_name
        new_user['username'] = message.from_user.username
        new_user['places'] = []
        users_collection.insert_one(new_user)


def user_data(user_id):
    return users_collection.find_one({'user_id': user_id})


def get_place(user_id, place_id):
    result = user_data(user_id)
    places = result['places']
    places.sort(key=itemgetter('date'), reverse=True)

    return places[int(place_id) - 1]


@bot.message_handler(commands=['start'])
def start_message(message):
    add_user(message)
    text = """\n\nВот, что я умею:\n/add - добавить новое место\n/list - вывести 10 последних добавленных мест
/reset - удалить все добавленные места\n/n - найти места в радиусе 500м от текущей локации"""

    bot.send_message(chat_id=message.chat.id, text='Приветствую, ' + message.from_user.first_name)
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['add'], content_types=['text'])
def add_place_handler(message):
    add_user(message)
    msg = bot.send_message(chat_id=message.chat.id, text='Давайте добавим информацию о новом месте. Сначала введите адрес')
    bot.register_next_step_handler(msg, add_place_address)


@bot.message_handler(commands=['list'])
def get_user_places(message):
    p = ''
    keyboard_keys = []
    result = user_data(message.from_user.id)

    if 'places' not in result.keys():
        bot.send_message(chat_id=message.chat.id, text='У вас нет ниодного добавленного места')
        return

    places = result['places']
    places.sort(key=itemgetter('date'), reverse=True)
    for number, place in enumerate(places):
        if number == 10:
            break
        p = p + (str(number + 1) + '. ' + place['address'] + '\n')
        keyboard_keys.append(number + 1)

    reply_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for key in keyboard_keys:
        reply_markup.add(str(key))
    msg = bot.send_message(chat_id=message.chat.id,
                           text='Последние добавленные места:\n\n' + p +
                                '\nВыберите номер для получения подробной информации',
                           reply_markup=reply_markup)

    bot.register_next_step_handler(msg, detailed_info)


@bot.message_handler(commands=['reset'])
def reset_user_places(message):
    result = user_data(message.from_user.id)

    if 'places' not in result.keys():
        bot.send_message(chat_id=message.chat.id, text='У вас нет ниодного добавленного места')
        return

    users_collection.update_one(
        {'user_id': message.from_user.id},
        {'$unset': {'places': ""}}
    )
    bot.send_message(chat_id=message.chat.id, text='Done')


@bot.message_handler(commands=['n'], content_types=['text'])
def current_location(message):
    msg = bot.send_message(chat_id=message.chat.id, text='Прикрепите ваше текущее местоположение')
    bot.register_next_step_handler(msg, get_nearest_places)


@bot.message_handler(content_types=['text', 'location', 'photo'])
def reply_to_input_outside_commands(message):
    bot.reply_to(message, 'Пожалуйста, воспользуйтесь командами бота')
    return


@bot.message_handler(content_types=['location'])
def get_nearest_places(message):
    if message.location is None:
        msg = bot.send_message(chat_id=message.chat.id, text='Прикрепите локацию!')
        bot.register_next_step_handler(msg, get_nearest_places)

    cur_location = (float(message.location.latitude), float(message.location.longitude))
    found_places = []
    p = ''
    result = user_data(message.from_user.id)

    if 'places' not in result.keys():
        bot.send_message(chat_id=message.chat.id, text='У вас нет ниодного добавленного места')
        return

    places = result['places']
    places.sort(key=itemgetter('date'), reverse=True)
    for number, place in enumerate(places):
        destination = (float(place['latitude']), float(place['longitude']))
        d = int(distance.distance(cur_location, destination).m)

        if d <= 500:
            number += 1
            p = p + (str(number) + '. ' + place['address'] + '\n')
            found_places.append(number)

    if len(found_places) == 0:
        bot.send_message(chat_id=message.chat.id, text='Поблизости нет мест из вашего списка')
        return

    reply_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for key in found_places:
        reply_markup.add(str(key))

    msg = bot.send_message(chat_id=message.chat.id,
                           text='Места поблизости:\n\n' + p +
                                '\nВыберите номер для получения подробной информации',
                           reply_markup=reply_markup)

    bot.register_next_step_handler(msg, detailed_info)


@bot.message_handler(content_types=['text'])
def detailed_info(message):
    chat_id = message.chat.id
    res = get_place(message.from_user.id, message.text)

    address = res['address']
    photo = res['file_id']
    latitude = res['latitude']
    longitude = res['longitude']

    bot.send_message(chat_id=chat_id, text='Адрес:\n' + address, reply_markup=telebot.types.ReplyKeyboardRemove())
    if photo != '-':
        bot.send_photo(chat_id=chat_id, photo=photo)
    bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)


@bot.message_handler(content_types=['text'])
def add_place_address(message):
    try:
        if message.text is None:
            msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, введите адрес текстом')
            bot.register_next_step_handler(msg, add_place_address)
            return

        new_place['address'] = message.text
        msg = bot.send_message(chat_id=message.chat.id, text="""Отлично! Далее загрузите фото или введите знак прочерка \"-\" если хотите пропустить этот шаг""")
        bot.register_next_step_handler(msg, add_place_photo)

    except Exception:
        msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Попробуйте снова...')
        bot.register_next_step_handler(msg, add_place_address)
        return


@bot.message_handler(content_types=['text', 'photo'])
def add_place_photo(message):
    try:
        if message.text is not None and message.text != '-':
            msg = bot.reply_to(message, 'Может быть вы хотели ввести прочерк "-"?')
            bot.register_next_step_handler(msg, add_place_photo)
            return

        elif message.text is not None and message.text == '-':
            msg = bot.send_message(chat_id=message.chat.id, text='Хорошо! Теперь добавьте локацию...')
            new_place['file_id'] = '-'
            bot.register_next_step_handler(msg, add_place_location)

        elif message.text is None and message.photo is None:
            print(message)
            msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, загрузите фото')
            bot.register_next_step_handler(msg, add_place_photo)
            return

        else:
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

        new_place['latitude'] = message.location.latitude
        new_place['longitude'] = message.location.longitude
        new_place['date'] = datetime.now()
        users_collection.update_one(
            {'user_id': message.from_user.id},
            {'$push': {'places': new_place}}
        )

        bot.send_message(chat_id=message.chat.id, text='Сохранено')
    except Exception as e:
        msg = bot.reply_to(message, 'Упс... Что-то пошло не так. Пожалуйста, прикрепите локацию')
        bot.register_next_step_handler(msg, add_place_location)
        return


if __name__ == '__main__':
    bot.enable_save_next_step_handlers(delay=2)
    bot.polling(none_stop=True, interval=0, timeout=20)
