import asyncio
import json
from geopy.geocoders import Nominatim
from random import randint

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor

import keyboards as kb
from config import TOKEN
from state import Register

bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

cancel_button = 'Отмена 🙅‍♂️'
pay_button = 'Оплатить 💵'
delivery_button = 'Заказать доставку 🏍'
phone_number_button = 'Отправить номер 📞'
location_button = 'Отправить местоположение 📍'
ordered_button = 'Завершить оформление ✅'


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
    await msg.answer('Заказ отменён', reply_markup=kb.make_order_button())
    await state.finish()


@dp.message_handler(Text(equals=pay_button))
async def pay(msg: types.Message):
    '''Оплата заказа'''
    tg_id = msg.from_user.id
    del_msg = await msg.answer('Проверка оплаты...')
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


@dp.message_handler(content_types='contact')
async def get_delivery_location(msg: types.Message):
    '''Запрос геолокации'''
    await msg.answer(
        f'Передайте Ваше местоположение для доставки заказа с помощью кнопки <b>{location_button}</b>',
        reply_markup=kb.get_location(cancel_button, location_button))


@dp.message_handler(content_types='location')
async def order_is_processed(msg: types.Message, state: FSMContext):
    '''Дополнительная информация'''
    latitude = msg.location.latitude
    longitude = msg.location.longitude
    await msg.answer(f'''
При необходимости укажите дополнительную информацию для курьера
(например код домофона, этаж, номер квартиры и др.)

Или завершите оформление заказа''',
        reply_markup=kb.menu_keyboard([cancel_button, ordered_button]),
        parse_mode ='HTML')
    geolocator = Nominatim(user_agent="cafe_demo_bot")
    location = geolocator.reverse(f'{latitude}, {longitude}')
    address = location.address.split(',')[0:4]
    address.reverse()
    await state.update_data(geo=' '.join(address))
    await Register.add_info.set()


@dp.message_handler(state=Register.add_info)
async def add_info(msg: types.Message, state: FSMContext):
    '''Изменить доп информацию или закончить оформление заказа'''
    states = await state.get_data()
    address = states.get('geo')
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
        await state.finish()
        await asyncio.sleep(30)
        with open('./img/courier.png', 'rb') as courier:
            await msg.answer_photo(
                courier, 
                caption=f'Ваш заказ <b>№ {randint(50, 200)}</b> готов и передан курьеру для доставки')
        await asyncio.sleep(60)
        with open('./img/locations.png', 'rb') as locations:
            await msg.answer_photo(locations, caption=f'''Курьер прибудет через 5 минут по адресу:
<b>{address}</b>''')
        await asyncio.sleep(60)
        with open('./img/checkout.png', 'rb') as checkout:
            await msg.answer_photo(
                checkout,
                caption='Ваш заказ доставлен.\nБлагодарим за выбор нашего сервиса!\nВ качестве подарка вам доступна скидка 10% на седующий заказ')
    else:
        await state.update_data(add_info=msg.text)
        await msg.answer(
            'Информация принята',
            reply_markup=kb.menu_keyboard([cancel_button, ordered_button]))


if __name__ == '__main__':
    executor.start_polling(dp)
