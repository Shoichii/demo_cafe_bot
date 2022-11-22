from aiogram.dispatcher.filters.state import State, StatesGroup


class Register(StatesGroup):
    total_price = State()
    phone_number = State()
    location = State()
    add_info = State()
    courier_location = State()
