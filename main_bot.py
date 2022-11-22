import asyncio
import json
from geopy.geocoders import Nominatim
from random import randint
import logging

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from utils import locationMsg, addressMsg, cancelMsg

import keyboards as kb
from config import TOKEN
from state import Register
import re

bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

cancel_button = 'Отмена 🙅‍♂️'
pay_button = 'Оплатить 💵'
delivery_button = 'Заказать доставку 🏍'
phone_number_button = 'Отправить номер 📞'
location_button = 'Отправить местоположение 📍'
ordered_button = 'Завершить оформление ✅'
rating_buttons = ['1 🌟', '2 🌟', '3 🌟', '4 🌟', '5 🌟']

logger = logging.getLogger(__name__)
logging.basicConfig(
    # filename=f'logs/logger.log',
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)
logger.addHandler(logging.StreamHandler())

@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    print(msg)
    with open('./img/onlineShopping.png', 'rb') as greeting_pic:
        await bot.send_photo(
            msg.from_user.id, greeting_pic,
            caption=f'''Приветствую тебя {msg.from_user.full_name}!

Я КафеБОТ, помогу заказать продукцию из нашего кафе и оформить доставку.

Приятного аппетита! 🍰''',
            reply_markup=kb.make_order_button())


@dp.message_handler(content_types='web_app_data')
async def get_order(msg: types.web_app_data, state: FSMContext):
    '''Получение заказа через WebApp и вывод его в сообщении'''
    data = json.loads(msg.web_app_data.data)
    products = data['products']
    total_cost = data['totalCost']
    result = 'Вы заказали:\n'
    for x in products:
        result += f"<b>{x['name']} {x['amount']}шт</b> на сумму: <b>{x['sumCost']} р</b>\n"
    result += f'\nОбщая стоимость: <b>{total_cost} р</b>'
    await msg.answer(
        result,
        reply_markup=kb.menu_keyboard([cancel_button, pay_button]))
    await state.update_data(total_price=total_cost)


@dp.message_handler(Text(equals=cancel_button))
async def cancle(msg: types.Message, state: FSMContext):
    '''Отмена заказа'''
    await cancelMsg.cancleMsg(msg, state, kb)


@dp.message_handler(Text(equals=pay_button))
async def pay(msg: types.Message):
    '''Оплата заказа'''
    tg_id = msg.from_user.id
    del_msg = await msg.answer('Проверка оплаты...', reply_markup=types.ReplyKeyboardRemove())
    del_sticker = await msg.answer_sticker('CAACAgIAAxkBAAEGfF5jew5DNZTWY9eYSB2eXIvLg2uZOgACdFsBAAFji0YM3S9lzUKXpDgrBA')
    await asyncio.sleep(4)
    await bot.delete_message(tg_id, del_msg.message_id)
    await bot.delete_message(tg_id, del_sticker.message_id)
    await msg.answer(
        'Оплата прошла успешно',
        reply_markup=kb.menu_keyboard([cancel_button, delivery_button]))


@dp.message_handler(Text(equals=delivery_button))
async def get_phone_number(msg: types.Message):
    '''Запрос номера телефона'''
    await msg.answer(
        f'''Для оформления доставки передайте номер телефона с помощью кнопки 

<b>{phone_number_button}</b>''',
        reply_markup=kb.get_contact(cancel_button, phone_number_button))
    await Register.phone_number.set()


@dp.message_handler(state=Register.phone_number, content_types=['contact', 'text'])
async def get_delivery_location(msg: types.Message, state: FSMContext):
    '''Запрос геолокации'''
    if msg.text == cancel_button:
        await state.finish()
        await cancelMsg.cancleMsg(msg, state, kb)
        return
    if not msg.contact:
        result = re.match(r'\b\+?[7,8](\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2})\b', msg.text)
        if not result:
            await msg.answer('Пожалуйста, введите корректный номер телефона.')
            return
        else:
            await addressMsg.addressMsg(msg, [cancel_button, location_button], kb)
    else:
        await addressMsg.addressMsg(msg, [cancel_button, location_button], kb)
    await Register.location.set()


@dp.message_handler(state=Register.location, content_types=['location', 'text'])
async def order_is_processed(msg: types.Message, state: FSMContext):
    '''Дополнительная информация'''
    geolocator = Nominatim(user_agent="cafe_demo_bot")
    if msg.text == cancel_button:
        await state.finish()
        await cancelMsg.cancleMsg(msg, state, kb)
        return
    if msg.location:
        latitude = msg.location.latitude
        longitude = msg.location.longitude
        location = geolocator.reverse(f'{latitude}, {longitude}')
        await state.update_data(courier_location=[location.latitude + 0.007, location.longitude + 0.005])
        address = location.address.split(',')[0:4]
        address.reverse()
        answer = f'''
При необходимости укажите дополнительную информацию для курьера
(например код домофона, этаж, номер квартиры и др.)

Или завершите оформление заказа'''
        await locationMsg.locationMsg(msg, answer, [cancel_button, ordered_button], state, kb, ' '.join(address))
    else:
        location = geolocator.geocode(msg.text)
        await state.update_data(courier_location=[location.latitude + 0.007, location.longitude + 0.005])
        answer = f'''
При необходимости укажите дополнительную информацию для курьера

Или завершите оформление заказа'''
        await locationMsg.locationMsg(msg, answer, [cancel_button, ordered_button], state, kb, msg.text)
    await Register.add_info.set()


@dp.message_handler(state=Register.add_info)
async def add_info(msg: types.Message, state: FSMContext):
    '''Изменить доп информацию или закончить оформление заказа'''
    if msg.text == cancel_button:
        await state.finish()
        await cancelMsg.cancleMsg(msg, state, kb)
        return
    states = await state.get_data()
    address = states.get('location')
    add_info = states.get('add_info')
    if add_info:
        message = f'''Заказ на сумму <b>{states.get('total_price')} руб.</b> успешно оформлен.
Ожидайте курьера по адресу 
<b>{address}</b>

Дополнительная информация для курьера:
<b>{states.get('add_info')}</b>'''
    else:
        message = f'''Заказ на сумму <b>{states.get('total_price')} руб.</b> успешно оформлен.
Ожидайте курьера по адресу
<b>{address}</b>'''
    if (msg.text == ordered_button or msg.text == cancel_button):
        await msg.answer(message, reply_markup=kb.make_order_button())

        await asyncio.sleep(5)
        with open('./img/courier.png', 'rb') as courier:
            await msg.answer_photo(
                courier, 
                caption=f'Ваш заказ <b>№ {randint(50, 200)}</b> готов и передан курьеру для доставки')

        await asyncio.sleep(5)
        with open('./img/locations.png', 'rb') as locations:
            await msg.answer_photo(locations, caption=f'''Курьер прибудет через 5 минут по адресу 
<b>{address}</b>''', reply_markup=kb.courier_location())
    else:
        await state.update_data(add_info=msg.text)
        await msg.answer(
            'Информация принята',
            reply_markup=kb.menu_keyboard([cancel_button, ordered_button]))


@dp.callback_query_handler(Text(equals='courier_location'))
async def courier_location(call: types.CallbackQuery, state: FSMContext):
    states = await state.get_data()
    courier_geo = states.get('courier_location')
    print(states, courier_geo)
    await bot.send_location(call.message.chat.id, courier_geo[0], courier_geo[1])
    await asyncio.sleep(5)
    with open('./img/checkout.png', 'rb') as checkout:
        await call.message.answer_photo(
                checkout, 
                caption='''Ваш заказ доставлен. Спасибо, что выбрали наш сервис. Вам доступна скидка 10% на седующий заказ

Пожалуйста, оцените нашу работу.''', reply_markup=kb.rating(rating_buttons))
    await state.finish()


@dp.callback_query_handler(Text(startswith='rating'))
async def rate(call: types.CallbackQuery):
    print(call)
    await call.answer('Спасибо за оценку!', show_alert=True)
    await call.message.edit_reply_markup()


if __name__ == '__main__':
    executor.start_polling(dp)
