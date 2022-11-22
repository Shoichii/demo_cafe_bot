from state import Register

async def locationMsg(msg, answer, kb_menu, state, kb, text):
    await msg.answer(answer,
            reply_markup=kb.menu_keyboard(kb_menu),
            parse_mode ='HTML')
    await state.update_data(geo=text)
    await Register.add_info.set()