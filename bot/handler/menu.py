import asyncio
import random
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import exceptions
from aiogram.utils.markdown import hide_link
from django.core.exceptions import ObjectDoesNotExist

from apps.location.models import Village, Area, Region
from bot.button.reply import menu_rkm
from bot.handler import db, MyStates, start_command
from bot.utils.log import log
from bot.utils.validator import strip_tags, format_testing_time, correct_answers_counter
from config.settings import WEB_SITE_URL


async def profile_handler(message: types.Message):
    try:
        user = await db.get_user(chat_id=message.chat.id)
        village = await Village.objects.aget(id=user.village_id)
        area = await Area.objects.aget(id=village.area_id)
        region = await Region.objects.aget(id=area.region_id)
        text = (
            f"<b>Sizning ma'lumotlaringiz:</b>\n\n"
            f"<b>F.I.Sh.:</b> {user.name}\n"
            f"<b>Tug‘ilgan yilingiz:</b> {user.age}\n"
            f"<b>Yashash manzilingiz:</b> {region.name}\n"
            f"<b>Tuman/shahar:</b> {area.name}\n"
            f"<b>Mahalla:</b> {village.name}\n"
            f"<b>Ish/o‘qish joyingiz:</b> {user.job_position}\n"
            f"<b>Telefon raqam: </b> {user.phone_number}\n"
        )

        await message.answer(text, reply_markup=menu_rkm())

    except ObjectDoesNotExist:
        await start_command(message)
    except Exception as e:
        log.error(f"line 40: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def testing_handler(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        if data == {}:
            chat_id = message.chat.id
            user = await db.get_user(chat_id=chat_id)
            tour = await db.get_tour()
            if tour is None:
                await message.answer(
                    "<b>Test ishlash boshlanganida e'lon qilamiz. \nBiz bilan bo'ling!</b>"
                )
            else:
                if await db.get_test(user.id, tour.id):
                    testing = await db.get_testing(user.id, tour.id)
                    await message.answer(
                        f"<b>Test yakunlandi!\nTo'g'ri javoblar soni: {testing.correct_answers_count} ta</b>"
                    )
                else:
                    try:
                        ikm_tour = InlineKeyboardMarkup(row_width=1)
                        await MyStates.question_state.set()
                        ikm_tour.add(
                            InlineKeyboardButton("🚀 Boshlash", callback_data="started")
                        )
                        await message.answer(
                            f"{tour.name}\n"
                            f"<b>Testlar soni</b>: {tour.count} ta"
                            f"\n{format_testing_time(tour.testing_time)} vaqt beriladi"
                            f"\n\nBitta to'plamni faqat bir marta ishlash imkoningiz bor",
                            reply_markup=ikm_tour,
                        )
                    except Exception as e:
                        log.error(
                            f"line 77: menu.py Target [ID:{message.chat.id}]: {e}"
                        )
        else:
            try:
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text="<b>Test yakunlandi!\nTo'g'ri javoblar soni: 7 ta</b>",
                    reply_to_message_id=data["message_id"],
                )
            except exceptions.MessageToReplyNotFound as e:
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text="<b>Test yakunlandi!\nTo'g'ri javoblar soni: 7 ta</b>",
                )
    except ObjectDoesNotExist:
        await start_command(message)
    except Exception as e:
        log.error(f"line 89: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def question_call_handler(call: types.CallbackQuery, state: FSMContext):
    try:
        if call.data == "started":
            await call.answer("")
            await MyStates.answers_state.set()
            await question_answer_handler(message=call.message, state=state)
    except Exception as e:
        log.error(
            f"line 108: menu.py Target [ID:{call.message.chat.id}]: {str(e).lower()}"
        )


async def stopped_test_time_async(time, state, message: types.Message):
    try:
        await asyncio.sleep(int(time.total_seconds()))
        data = await state.get_data()
        correct_answers_count = correct_answers_counter(data)
        user = await db.get_user(chat_id=message.chat.id)
        tour = await db.get_tour()
        if not await db.get_test(user.id, tour.id):
            if not data == {}:
                await state.finish()
                user = await db.get_user(chat_id=message.chat.id)
                testing_datetime = datetime.combine(datetime.min, tour.testing_time)
                speling_time = (
                    testing_datetime
                    - (data["questions"][0]["finished_at"] - datetime.now())
                ).strftime("%H:%M:%S")
                await message.edit_text(
                    f"Test yakunlandi!\n"
                    f"{tour.name}\n"
                    f"<b>To'g'ri javoblar soni:</b> {correct_answers_count} ta\n\n"
                    f"Keyingi turlarni e'lon qilib boramiz. Biz bilan qoling!"
                )
                testing = await db.create_testing(
                    tg_user_id=user.id,
                    tour_id=tour.id,
                    started_at=data["questions"][0]["started_at"],
                    finished_at=data["questions"][0]["finished_at"],
                    spent_time=speling_time,
                    count_answers=correct_answers_count,
                )
                for question in data["questions"]:
                    await db.create_answers(
                        tg_user_id=user.id,
                        tour_id=tour.id,
                        testing_id=testing.id,
                        question_id=question["id"],
                        received_answer=data["user_answers"],
                    )
    except Exception as e:
        log.error(f"line 144: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


def stopped_test_time(time, state, message: types.Message):
    loop = asyncio.get_event_loop()
    loop.create_task(stopped_test_time_async(time, state, message))


async def question_answer_handler(message: types.Message, state: FSMContext):
    try:
        questions = await formated_question(message=message)
        time = questions[0]["finished_at"] - questions[0]["started_at"]
        stopped_test_time(time, state, message=message)

        first_question = questions[0]
        await send_question(first_question["text"], message=message)
        await state.update_data(
            question_id=0,
            questions=questions,
            count=len(questions),
            correct_answers_count=0,
            user_answers={},
            message_id=message.message_id,
        )
        await state.set_state(None)
    except Exception as e:
        log.error(f"line 164: menu.py Target [ID:]: {str(e).lower()}")


async def send_question(question_text, message: types.Message):
    design = [
        [
            InlineKeyboardButton("A", callback_data="answer:A"),
            InlineKeyboardButton("B", callback_data="answer:B"),
            InlineKeyboardButton("C", callback_data="answer:C"),
            InlineKeyboardButton("D", callback_data="answer:D"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=design, row_width=4)
    try:
        if isinstance(message, types.CallbackQuery):
            await message.message.edit_text(text=question_text, reply_markup=keyboard)
        else:
            await message.edit_text(text=question_text, reply_markup=keyboard)
    except Exception as e:
        log.error(f"line 179: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def process_answer(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("")
    selected_option = callback_query.data.split(":")[1]
    data = await state.get_data()
    try:
        if data == {}:
            await callback_query.message.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
            )
            await callback_query.message.answer(
                text="<b>Siz joriy turda ishtirok etgansiz. Keyingi turlarni kuting!</b>"
            )
        else:
            data["user_answers"].update({data["question_id"]: selected_option})
            await state.update_data(user_answers=data["user_answers"])
            if (
                data["count"] - 1 == data["question_id"]
                or data["questions"][0]["finished_at"] <= datetime.now()
            ):
                await state.finish()
                correct_answers_count = correct_answers_counter(data)
                user = await db.get_user(chat_id=callback_query.message.chat.id)
                tour = await db.get_tour()
                testing_datetime = datetime.combine(datetime.min, tour.testing_time)
                speling_time = (
                    testing_datetime
                    - (data["questions"][0]["finished_at"] - datetime.now())
                ).strftime("%H:%M:%S")
                tour = await db.get_tour()
                testing = await db.create_testing(
                    tg_user_id=user.id,
                    tour_id=tour.id,
                    started_at=data["questions"][0]["started_at"],
                    finished_at=data["questions"][0]["finished_at"],
                    spent_time=speling_time,
                    count_answers=correct_answers_count,
                )

                await db.create_answers_bulk(
                    tg_user_id=user.id,
                    tour_id=tour.id,
                    testing_id=testing.id,
                    answers=data["questions"],
                    user_answer=data["user_answers"],
                )
                await callback_query.message.edit_text(
                    f"Test yakunlandi!\n"
                    f"{tour.name}\n"
                    f"<b>To'g'ri javoblar soni:</b> {correct_answers_count} ta\n\n"
                    f"Keyingi turlarni e'lon qilib boramiz. Biz bilan qoling!"
                )
            else:
                await send_question(
                    data["questions"][data["question_id"] + 1]["text"],
                    message=callback_query.message,
                )
                await state.update_data(question_id=data["question_id"] + 1)
    except Exception as e:
        log.error(
            f"line 233: menu.py Target [ID:{callback_query.message.chat.id}]: {str(e).lower()}"
        )


async def formated_question(message: types.Message):
    chat_id = (
        message.message.chat.id
        if isinstance(message, types.CallbackQuery)
        else message.chat.id
    )
    try:
        tour = await db.get_tour()
        started_at, testing_datetime = datetime.now(), datetime.combine(
            datetime.min, tour.testing_time
        )
        finished_at = started_at + timedelta(
            hours=testing_datetime.hour,
            minutes=testing_datetime.minute,
            seconds=testing_datetime.second,
        )
        questions = []
        question = await db.get_questions_by_tour(tour_id=tour.id)
        random.shuffle(question)
        for i, q in enumerate(question[: tour.count]):
            options = [
                q.correct_answer,
                q.incorrect_answer_1,
                q.incorrect_answer_2,
                q.incorrect_answer_3,
            ]
            random.shuffle(options)
            correct_answer_index = options.index(q.correct_answer)
            correct_answer = chr(ord("A") + correct_answer_index)

            text = f'Test {finished_at.time().strftime("%H:%M")} da yakunlanadi\n\n<b>{i + 1}-test. {q.text}</b>\n\n'
            if str(q.photo).startswith("questions/"):
                text += f'{hide_link(WEB_SITE_URL + "media/" + str(q.photo))}'

            text += (
                f"A) {options[0]}\nB) {options[1]}\nC) {options[2]}\nD) {options[3]}"
            )

            d = {
                "question_id": i,
                "text": text,
                "correct_option": correct_answer,
                "started_at": started_at,
                "finished_at": finished_at,
                "id": q.id,
                "options": options,
            }

            questions.append(d)
        return questions
    except Exception as e:
        log.error(f"line 273: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def results_handler(message: types.Message, state: FSMContext):
    try:
        test = await db.top_tiers_users(chat_id=message.chat.id)
        str_top = f"{test['tour_name']}\n\n"
        if 1 <= test["index"] <= 30 and not test["index"] == 0:
            for idx, result in enumerate(test["testings"], 1):
                user = await db.get_user_by_id(id=result["user"])
                if str(user.chat_id) == str(message.chat.id):
                    str_top += f"{idx}) {user.name} - {result['score']} ball 👏\n"
                else:
                    str_top += f"{idx}) {user.name} - {result['score']} ball\n"
        elif not test["index"] == 0:
            for idx, result in enumerate(test["testings"], 1):
                user = await db.get_user_by_id(id=result["user"])
                str_top += f"{idx}) {user.name} - {result['score']} ball\n"
            user = await db.get_user(message.chat.id)
            str_top += f"...\n{test['index']}) {user.name} - {test['current_user_score']} ball 👏"
        else:
            for idx, result in enumerate(test["testings"], 1):
                user = await db.get_user_by_id(id=result["user"])
                str_top += f"{idx}) {user.name} - {result['score']} ball\n"
            str_top += "\nIshtirok etish uchun 👉 /start"
        await message.answer(str_top)
    except ObjectDoesNotExist:
        await start_command(message)
    except Exception as e:
        log.error(f"line 312: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


#
#     try:
#         # Global top tiers
#         test = await db.global_top_tiers_users(chat_id=message.chat.id)
#         str_top_global = f"<b>{test['subject_name']}:</b> Umumiy natija\n\n"
#         if 1 <= test['index'] <= 30 and not test['index'] == 0:
#             for idx, result in enumerate(test['testings'], 1):
#                 user = await db.get_user_by_id(id=result['user'])
#                 if str(user.chat_id) == str(message.chat.id):
#                     str_top_global += f"{idx}) {user.name} - {result['score']} ball 👏\n"
#                 else:
#                     str_top_global += f"{idx}) {user.name} - {result['score']} ball\n"
#         elif not test['index'] == 0:
#             for idx, result in enumerate(test['testings'], 1):
#                 user = await db.get_user_by_id(id=result['user'])
#                 str_top_global += f"{idx}) {user.name} - {result['score']} ball\n"
#             user = await db.get_user(message.chat.id)
#             str_top_global += f"...\n{test['index']}) {user.name} - {test['current_user_score']} ball 👏"
#         else:
#             for idx, result in enumerate(test['testings'], 1):
#                 user = await db.get_user_by_id(id=result['user'])
#                 str_top_global += f"{idx}) {user.name} - {result['score']} ball\n"
#             str_top_global += "\nIshtirok etish uchun 👉 /start"
#         await message.answer(str_top_global)
#     except ObjectDoesNotExist:
#         await start_command(message)
#     except Exception as e:
#         log.error(f"line 334: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")


async def info_handler(message: types.Message):
    try:
        infos = await db.get_info_by_slug("info-text")
        info_text = strip_tags(infos.content)
    except ObjectDoesNotExist as e:
        info_text = "Bu bolim ishlamayapti"
    try:
        await message.answer(f"{info_text}", disable_web_page_preview=True)
    except ObjectDoesNotExist:
        await start_command(message)
    except Exception as e:
        log.error(f"line 332: menu.py Target [ID:{message.chat.id}]: {str(e).lower()}")
