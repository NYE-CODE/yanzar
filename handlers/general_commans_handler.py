

@dp.message_handler(Text(equals=["Назад 🔙", "Отменить ❌"]), state="*")
async def back_or_cancel_commands(message: types.Message, state: FSMContext):
    if state:
        await state.reset_state()

    last_message = message.message_id - 2
    await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message)

    main_keyboard = await generate_main_keyboard(BotConfig.is_admin)
    exit_message = "Вы вышли из вкладки 'Сигвеи 🛴'"
    await message.answer(exit_message, reply_markup=main_keyboard)