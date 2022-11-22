from state import Register

async def locationMsg(msg, answer, kb_menu, state, kb, text):
    await msg.answer(answer,
        reply_markup=kb.menu_keyboard(kb_menu))
    await state.update_data(location=text)
    await Register.add_info.set()