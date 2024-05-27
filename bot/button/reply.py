from datetime import datetime

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.button.text import *


def register_rkm():
    design = [["Ro'yxatdan o'tish"]]
    return ReplyKeyboardMarkup(
        keyboard=design, resize_keyboard=True, one_time_keyboard=True
    )


def phone_rkm():
    design = [[KeyboardButton("📞 Yuborish", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)


def age_rkm():
    today = datetime.today()
    age_list = [
        [str(today.year - 25), str(today.year - 24)],
        [str(today.year - 23), str(today.year - 22)],
        [str(today.year - 21), str(today.year - 20)],
        [str(today.year - 19), str(today.year - 18)],
    ]  # only for 18 - 25 year
    return ReplyKeyboardMarkup(keyboard=age_list, resize_keyboard=True)


def menu_rkm():
    design = [
        [testing_text, results_text],
        [profile_text, info_text],
    ]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)
