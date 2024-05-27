import datetime
import re
from datetime import timedelta


def validate_uzbek_phone_number(phone_number):
    pattern = re.compile(r"^998\d{9}$")
    qpattern = re.compile(r"^\+998\d{9}$")

    return bool(pattern.match(phone_number) or qpattern.match(phone_number))


def validate_full_name(full_name: str):
    if full_name.startswith("📝 Ro'yxatdan"):
        return False
    if len(full_name.split(" ")) > 2:
        return True
    else:
        return False


def validate_date_of_birth(year):
    try:
        if (int(datetime.datetime.now().year) - int(year)) > 100:
            return False
        return True
    except ValueError as e:
        return False


def strip_tags(html):
    replaced_html = re.sub(r"<(/p).*?>|<(p).*?>|<(br).*?>", "", html)
    replaced_html = replaced_html.replace("<em>", "<i>").replace("</em>", "</i>")
    replaced_html = replaced_html.replace("<strong>", "<b>").replace(
        "</strong>", "</b>"
    )
    return replaced_html


def custom_title_case(s: str):
    result = s.split(maxsplit=2)
    name = ""
    for i in result:
        i = i[0].upper() + i[1:]
        name += i + " "
    return name


def format_testing_time(testing_time):
    testing_time_timedelta = timedelta(
        hours=testing_time.hour,
        minutes=testing_time.minute,
        seconds=testing_time.second,
    )

    days, seconds = divmod(testing_time_timedelta.total_seconds(), 86400)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    formatted_time = ""
    if days:
        formatted_time += f"{int(days)} kun "
    if hours:
        formatted_time += f"{int(hours)} soat "
    if minutes:
        formatted_time += f"{int(minutes)} daqiqa "
    if seconds:
        formatted_time += f"{int(seconds)} sekunda"

    return formatted_time.strip()


def correct_answers_counter(data):
    user_answers = data.get("user_answers", {})
    questions = data.get("questions", [])

    correct_answers_count = 0

    for question in questions:
        question_id = question.get("question_id")
        correct_option = question.get("correct_option")
        user_answer = user_answers.get(question_id)

        if user_answer and user_answer == correct_option:
            correct_answers_count += 1

    return correct_answers_count
