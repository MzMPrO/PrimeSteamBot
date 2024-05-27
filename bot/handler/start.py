import datetime
import os

import django

from bot.utils.log import log
from bot.utils.validator import (
    validate_full_name,
    validate_date_of_birth,
    validate_uzbek_phone_number,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from django.core.exceptions import ObjectDoesNotExist
from apps.location.models import Village, Area, Region
from apps.users.models import RegistrationData, TelegramUser
from bot.button.reply import register_rkm, menu_rkm, phone_rkm
from bot.db.main import PostgresqlDb

db = PostgresqlDb()


class MyStates(StatesGroup):
    register_state = State()
    enter_name_state = State()
    enter_phone_state = State()

    post_state = State()
    forward_type_state = State()
    confirm_state = State()

    subject_state = State()
    question_state = State()
    answers_state = State()


async def start_command(message: types.Message):
    # check if user is existed or not
    try:
        user = await db.get_user(chat_id=message.chat.id)
    except ObjectDoesNotExist as e:
        user = None
    if user is None:
        # check user send message from bot or not
        if not message.chat.type == "private":
            await db.create_user(
                name=message.chat.title,
                first_name=message.chat.first_name,
                last_name=message.chat.last_name,
                username=message.chat.username,
                chat_id=message.chat.id,
                type=message.chat.type,
            )
        else:
            try:
                info_text = await db.get_info_by_slug("start-text")
            except ObjectDoesNotExist as e:
                info_text = f""" <b>"Mahalla Tanlov" tanlovida ishtirok etish uchun avval ro'yxatdan o'ting></b> """
            if not info_text:
                info_text = f"""
                <b>"Mahalla Tanlov" tanlovida ishtirok etish uchun avval ro'yxatdan o'ting></b>"""
            await message.answer(
                f"{info_text}",
                reply_markup=register_rkm(),
                disable_web_page_preview=True,
            )
            await RegistrationData.objects.filter(chat_id=message.chat.id).adelete()
            await RegistrationData.objects.acreate(chat_id=message.chat.id)
    else:
        if message.chat.type == "private":
            info_text = "Botdan to'liq foydalanishingiz mumkin"
            await message.answer(f"{info_text}", reply_markup=menu_rkm())


async def cmd_register(message: types.Message):
    chat_id = message.chat.id
    await RegistrationData.objects.filter(chat_id=chat_id).adelete()
    await RegistrationData.objects.acreate(chat_id=chat_id)
    await message.answer(
        "<b>Familiya, ism, sharfingizni to'liq kiriting</b> \n(Abdullayev Abdulla Abdullayevich)",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def registration_process(message: types.Message):
    chat_id = message.chat.id
    reg_data = await RegistrationData.objects.aget(chat_id=chat_id)

    if not reg_data.name:
        if validate_full_name(message.text):
            reg_data.name = message.text
            await reg_data.asave()
            await message.answer("<b>Tug‘ilgan yilingizni kiriting</b> \n(2004)")
        else:
            await message.answer(
                "<b>Familiya, ism, sharfingizni to'liq kiriting</b> \n(Abdullayev Abdulla Abdullayevich)"
            )
    elif not reg_data.age:
        try:
            if validate_date_of_birth(message.text):
                reg_data.age = int(message.text)
                await reg_data.asave()
                await message.answer(
                    "<b>Yashash manzilingiz</b> \n(Hududingizni tanlang)",
                    reply_markup=await generate_keyboard(Region.objects.all()),
                )
            else:
                await message.answer("<b>Tug‘ilgan yilingizni kiriting</b> \n(2004)")
        except ValueError:
            await message.answer(
                "<b>Iltimos, tug'ilgan yilingizni to'g'ri kiriting.</b>"
            )
    elif not reg_data.region_id:
        try:
            region = await Region.objects.aget(name=message.text)
            reg_data.region = region
            await reg_data.asave()
            await message.answer(
                "<b>Tuman/shaharni tanlang</b>",
                reply_markup=await generate_keyboard(
                    Area.objects.filter(region_id=region.id)
                ),
            )
        except Region.DoesNotExist:
            await message.answer("<b>Yaroqli hududni tanlang.</b>")
    elif not reg_data.area_id:
        try:
            area = await Area.objects.aget(
                name=message.text, region_id=reg_data.region_id
            )
            reg_data.area = area
            await reg_data.asave()
            await message.answer(
                "<b>Mahallangizni tanlang</b>",
                reply_markup=await generate_keyboard(
                    Village.objects.filter(area_id=area.id)
                ),
            )
        except Area.DoesNotExist:
            await message.answer("<b>Yaroqli tuman yoki shaharni tanlang.</b>")
    elif not reg_data.village_id:
        try:
            village = await Village.objects.aget(
                name=message.text, area_id=reg_data.area_id
            )
            reg_data.village = village
            await reg_data.asave()
            await message.answer(
                "<b>Ish/o‘qish joyingiz va lavozimingizni kiriting</b>",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        except Village.DoesNotExist:
            await message.answer("<b>Yaroqli mahallani tanlang.</b>")
    elif not reg_data.job_position:
        reg_data.job_position = message.text
        await reg_data.asave()
        await message.answer(
            "<b>Aloqa uchun telefon raqamingizni qoldiring</b>",
            reply_markup=phone_rkm(),
        )
    elif not reg_data.phone_number:
        if message.content_type == "text":
            if validate_uzbek_phone_number(message.text):
                reg_data.phone_number = message.text
                await reg_data.asave()
                await complete_registration(message, reg_data, chat_id)
            else:
                await message.answer(
                    "<b>Aloqa uchun telefon raqamingizni qoldiring</b>"
                )
        else:
            if validate_uzbek_phone_number(message.contact.phone_number):
                reg_data.phone_number = message.contact.phone_number
                await reg_data.asave()
                await complete_registration(message, reg_data, chat_id)
            else:
                await message.answer("Aloqa uchun telefon raqamingizni qoldiring")


async def complete_registration(message, reg_data, chat_id):
    await TelegramUser.objects.acreate(
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
        username=message.chat.username,
        chat_id=chat_id,
        language_code=message.from_user.language_code,
        type=message.chat.type,
        name=reg_data.name,
        phone_number=reg_data.phone_number,
        age=reg_data.age,
        village_id=reg_data.village_id,
        job_position=reg_data.job_position,
    )

    await reg_data.adelete()
    await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz", reply_markup=menu_rkm())


async def any_message_handler(message: types.Message, state: FSMContext):
    try:
        await start_command(message)
    except Exception as e:
        log.error(f"line 339: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def generate_keyboard(model):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for instance in [instance async for instance in model]:
        keyboard.add(types.KeyboardButton(instance.name))
    return keyboard
