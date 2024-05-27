import logging

from aiogram import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType
from bot.button.text import *
from bot.dispacher import dp
from bot.handler import *
from bot.handler.menu import *
from bot.handler.post import *
from bot.middlewares.check_user import PremiumMiddleware, process_subscription_check
from bot.utils.filters import *


async def check_registration_exists(message):
    return await RegistrationData.objects.filter(chat_id=message.chat.id).aexists()


dp.filters_factory.bind(IsAdminFilter)

dp.register_message_handler(post_command, is_admin=True, commands=["post"])
dp.register_message_handler(
    post_handler,
    is_admin=True,
    state=MyStates.post_state,
    content_types=types.ContentType.ANY,
)
dp.register_message_handler(
    forward_type_forward_handler,
    Text(equals="Ha"),
    is_admin=True,
    state=MyStates.forward_type_state,
)
dp.register_message_handler(
    forward_type_copy_handler,
    Text(equals="Yo'q"),
    is_admin=True,
    state=MyStates.forward_type_state,
)
dp.register_message_handler(
    confirm_yes_handler, Text(equals="Ha"), is_admin=True, state=MyStates.confirm_state
)
dp.register_message_handler(
    confirm_no_handler, Text(equals="Yo'q"), is_admin=True, state=MyStates.confirm_state
)

dp.register_message_handler(start_command, commands=["start"], state="*")
dp.register_message_handler(
    cmd_register, lambda message: message.text == "Ro'yxatdan o'tish"
)
dp.register_message_handler(
    registration_process, check_registration_exists, content_types=ContentType.ANY
)


dp.register_message_handler(profile_handler, Text(profile_text))
dp.register_message_handler(info_handler, Text(info_text))
dp.register_message_handler(results_handler, Text(results_text))

dp.register_message_handler(testing_handler, Text(equals=testing_text), state="*")
dp.register_callback_query_handler(question_call_handler, state=MyStates.question_state)
dp.register_callback_query_handler(
    question_answer_handler, state=MyStates.answers_state
)
dp.register_callback_query_handler(
    process_answer, lambda c: c.data.startswith("answer:")
)

dp.register_callback_query_handler(
    process_subscription_check, lambda c: c.data == "check_subscription"
)

dp.register_message_handler(any_message_handler, content_types=ContentType.ANY)

# Middlewares
dp.setup_middleware(PremiumMiddleware())


async def set_my_commands(dp):
    commands = [
        types.BotCommand(command="/start", description="Botni qayta ishga tushirish"),
    ]
    await dp.bot.set_my_commands(commands)


def run_tg_bot():
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True, on_startup=set_my_commands)
