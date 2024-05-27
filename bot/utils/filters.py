from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import ChatMemberStatus, InlineKeyboardButton, InlineKeyboardMarkup

from bot.handler import db
from bot.utils.log import log


class IsAdminFilter(BoundFilter):
    key = "is_admin"

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message) -> bool:
        user = await db.get_user(chat_id=message.chat.id)
        return user.is_admin == self.is_admin
