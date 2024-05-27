from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import exceptions
from django.core.exceptions import ObjectDoesNotExist

from bot.dispacher import dp
from bot.handler import db, start_command


async def check_subscription(user_id: int, message: types.Message):
    try:
        member = await db.get_user(chat_id=message.chat.id)
        if member.is_white_list:
            return True
    except ObjectDoesNotExist as e:
        pass

    channels = await db.get_channels()
    for channel in channels:
        try:
            member = await message.bot.get_chat_member(
                chat_id="@" + channel.username, user_id=user_id
            )
            if member.status in ["member", "administrator", "creator"]:
                pass
            else:
                return False
        except exceptions.BadRequest as e:
            pass
    return True


async def process_subscription_check(
    callback_query: types.CallbackQuery, state: FSMContext
):
    user_id = callback_query.from_user.id
    is_subscribed = await check_subscription(user_id, message=callback_query.message)

    if is_subscribed:
        await callback_query.message.bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
        )
        await start_command(callback_query.message)
    else:
        await callback_query.answer("Avval kanallarga obuna bo'ling.", show_alert=True)


class PremiumMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if update.message:
            user_id = update.message.from_user.id
            is_subscribed = await check_subscription(
                user_id=user_id, message=update.message
            )
            if not is_subscribed:
                keyboard = InlineKeyboardMarkup(row_width=1)
                channels = await db.get_channels()
                for channel in channels:
                    keyboard.add(
                        InlineKeyboardButton(
                            f"Obuna bolish",
                            url=f"https://t.me/{channel.username.lstrip('@')}",
                        )
                    )
                keyboard.add(
                    InlineKeyboardButton(
                        "Tekshirish", callback_data="check_subscription"
                    )
                )
                await update.message.answer(
                    "Avval kanallarga obuna bo'ling:", reply_markup=keyboard
                )
                raise CancelHandler()

        elif update.callback_query:
            try:
                if update.callback_query.data == "started":
                    state = dp.current_state(user=update.callback_query.message.chat.id)
                    if await state.get_state() is not None:
                        pass
                    else:
                        await update.callback_query.message.bot.delete_message(
                            chat_id=update.callback_query.message.chat.id,
                            message_id=update.callback_query.message.message_id,
                        )
            except Exception as e:
                pass
