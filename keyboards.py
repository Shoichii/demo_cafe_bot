from aiogram import types

from config import URL_REACT_APP


def make_order_button():
    url = types.WebAppInfo(url=URL_REACT_APP)
    button = types.KeyboardButton(text="Сделать заказ 🍕", web_app=url)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button)
    return keyboard


def menu_keyboard(array: list, row_width=2):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       row_width=row_width)
    markup.add(*array)
    return markup


def get_contact(cancel, phone_number_button):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,)
    button = types.KeyboardButton(text=phone_number_button,
                                  request_contact=True)
    markup.row(cancel, button)
    return markup


def get_location(cancel, location_button):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,)
    button = types.KeyboardButton(text=location_button,
                                  request_location=True)
    markup.row(cancel, button)
    return markup
