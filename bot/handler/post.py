from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import exceptions
import asyncio

from bot.button.reply import menu_rkm
from bot.handler import db, MyStates
from bot.utils.log import log


async def post_command(message: types.Message):
    users_count = await db.get_users_count()
    await message.answer(
        f"{users_count} ta obunachiga yubormoqchi bo'lgan xabaringizni yuboring"
    )
    await MyStates.post_state.set()


async def post_handler(message: types.Message, state: FSMContext):
    from_chat_id = message.chat.id
    message_id = message.message_id
    await state.update_data(from_chat_id=from_chat_id, message_id=message_id)
    confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Ha", "Yo'q")
    await message.answer(
        "Xabar kimdan yuborilgani ko'rinsinmi?", reply_markup=confirm_keyboard
    )
    await MyStates.forward_type_state.set()


async def forward_type_forward_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=data["from_chat_id"],
        message_id=data["message_id"],
    )
    await state.update_data(forward_type="forward")
    confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Ha", "Yo'q")
    await message.answer(
        "Shu xabar yuborilishini tasdiqlaysizmi?", reply_markup=confirm_keyboard
    )
    await MyStates.confirm_state.set()


async def forward_type_copy_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=data["from_chat_id"],
        message_id=data["message_id"],
    )
    await state.update_data(forward_type="copy")
    confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Ha", "Yo'q")
    await message.answer(
        "Shu xabar yuborilishini tasdiqlaysizmi?", reply_markup=confirm_keyboard
    )
    await MyStates.confirm_state.set()


async def confirm_yes_handler(message: types.Message, state: FSMContext):
    await message.answer("Xabar yuborilyapti...", reply_markup=ReplyKeyboardRemove())
    data = await state.get_data()
    users = await db.get_users()
    successful, blocked, not_found, deactivated = 0, 0, 0, 0

    for user_id in users:
        try:
            await message.bot.forward_message(
                chat_id=user_id.chat_id,
                from_chat_id=data["from_chat_id"],
                message_id=data["message_id"],
            ) if data["forward_type"] == "forward" else await message.bot.copy_message(
                chat_id=user_id.chat_id,
                from_chat_id=data["from_chat_id"],
                message_id=data["message_id"],
            )

            successful += 1
            await db.update_user_status(status="active", chat_id=user_id.chat_id)
            if successful % 1000 == 0:
                await message.answer(
                    f"Xabar {successful} ta obunachiga yuborildi. Qolgan obunachilarga ham yuborilyapti..."
                )

            await asyncio.sleep(0.05)
        except (
            exceptions.BotBlocked,
            exceptions.UserDeactivated,
            exceptions.TelegramAPIError,
        ) as e:
            log.error(f"Target [ID:{user_id.chat_id}]: {str(e).lower()}")
            if isinstance(e, exceptions.BotBlocked):
                blocked += 1
                await db.update_user_status(status="blocked", chat_id=user_id.chat_id)
            elif isinstance(e, exceptions.UserDeactivated):
                deactivated += 1
                await db.update_user_status(
                    status="deactivated", chat_id=user_id.chat_id
                )
            elif isinstance(e, exceptions.ChatNotFound):
                not_found += 1
                await db.update_user_status(status="not_found", chat_id=user_id.chat_id)
                log.error(f"Target [ID:{user_id.chat_id}]: invalid user ID")

    await message.answer(
        f"Xabar {successful} ta obunachiga muvaffaqiyatli yuborildi\nBloklangan: {blocked}\nO'chirilgan: {deactivated}\nChat topilmadi: {not_found}",
        reply_markup=menu_rkm(),
    )
    log.info(f"{successful} messages successful sent.")
    await state.finish()


async def confirm_no_handler(message: types.Message, state: FSMContext):
    await message.answer("Xabar yuborish bekor qilindi!", reply_markup=menu_rkm())
    await state.finish()
