from state import Register

async def addressMsg(msg,buttons, kb):
    await msg.answer(
                f'''Передайте Ваше местоположение для доставки заказа с помощью кнопки <b>{buttons[1]}</b>
или введите адрес вручную''',
                reply_markup=kb.get_location(buttons[0], buttons[1]))
    await Register.location.set()