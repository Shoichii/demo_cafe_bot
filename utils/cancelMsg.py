async def cancleMsg(msg, state, kb):
    await msg.answer('Заказ отменён', reply_markup=kb.make_order_button())
    await state.finish()