from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.utils import timezone

from apps.questions.models import Tour, Question
from apps.user_answers.models import Testing, Answer
from apps.users.models import TelegramUser, Channels, Info
from bot.utils.log import log


class PostgresqlDb:
    def __init__(self):
        pass

    @staticmethod
    async def get_users():
        users = TelegramUser.objects.all()
        return [user async for user in users]

    @staticmethod
    async def create_user(
        first_name,
        last_name,
        username,
        chat_id,
        age=None,
        village=None,
        language_code=None,
        name=None,
        phone_number=None,
        type="private",
    ):
        return await TelegramUser.objects.acreate(
            first_name=first_name,
            last_name=last_name,
            username=username,
            chat_id=chat_id,
            language_code=language_code,
            name=name,
            age=age,
            village_id=village,
            phone_number=phone_number,
            type=type,
        )

    @staticmethod
    async def get_user(chat_id):
        return await TelegramUser.objects.aget(chat_id=chat_id)

    @staticmethod
    async def get_user_by_id(id: int):
        return await TelegramUser.objects.aget(id=id)

    @staticmethod
    async def get_users_count():
        return await TelegramUser.objects.acount()

    @staticmethod
    async def update_user_status(chat_id: int | str, status: str):
        await TelegramUser.objects.filter(chat_id=chat_id).aupdate(status=status)

    @staticmethod
    async def get_channels():
        channels = Channels.objects.filter(is_active=True).order_by("order")
        return [channel async for channel in channels]

    @staticmethod
    async def get_info_by_slug(slug: str):
        return await Info.objects.aget(slug=slug)

    @staticmethod
    async def get_tour():
        now = timezone.now()
        return (
            await Tour.objects.filter(start_time__lt=now, end_time__gt=now)
            .order_by("-created_at")
            .afirst()
        )

    @staticmethod
    async def get_questions_by_tour(tour_id: int):
        now = timezone.now()
        tour = (
            await Tour.objects.filter(start_time__lt=now, end_time__gt=now)
            .order_by("-end_time")
            .afirst()
        )
        questions = Question.objects.filter(tour_id=tour_id, is_active=True)[
            : tour.count
        ]
        return [question async for question in questions]

    @staticmethod
    async def create_testing(
        tg_user_id,
        tour_id,
        started_at,
        finished_at,
        spent_time: str = 0,
        count_answers=0,
    ):
        created_testing = await Testing.objects.acreate(
            tg_user_id=tg_user_id,
            tour_id=tour_id,
            started_at=started_at,
            finished_at=finished_at,
            spent_time=spent_time,
            correct_answers_count=count_answers,
        )
        retrieved_testing = await Testing.objects.aget(id=created_testing.id)
        return retrieved_testing

    @staticmethod
    async def get_test(tg_user_id, tour_id):
        return await Testing.objects.filter(
            tg_user_id=tg_user_id, tour_id=tour_id
        ).aexists()

    @staticmethod
    async def get_testing(tg_user_id, tour_id):
        return await Testing.objects.filter(
            tg_user_id=tg_user_id, tour_id=tour_id
        ).afirst()

    @staticmethod
    async def create_answers(
        tg_user_id, tour_id, testing_id, question_id, received_answer
    ):
        created_answers = await Answer.objects.acreate(
            tg_user_id=tg_user_id,
            tour_id=tour_id,
            testing_id=testing_id,
            question_id=question_id,
            received_answer=received_answer[question_id],
        )
        retrieved_answers = await Answer.objects.aget(id=created_answers.id)
        return retrieved_answers

    @staticmethod
    async def create_answers_bulk(
        tg_user_id, tour_id, testing_id, answers, user_answer
    ):
        # print(f"User: {tg_user_id}\n"
        #       f"Tour: {tour_id}\n"
        #       f"Testing_id: {testing_id}\n"
        #       f"Answers: {answers}")
        # print(answers, user_answer)
        answer_objects = [
            Answer(
                tg_user_id=tg_user_id,
                tour_id=tour_id,
                testing_id=testing_id,
                question_id=question["id"],
                received_answer=question["options"][
                    ord(user_answer[question["question_id"]]) - ord("A")
                ],
            )
            for question in answers
        ]
        await Answer.objects.abulk_create(answer_objects)

    @staticmethod
    async def top_tiers_users(chat_id):
        try:
            now = timezone.now()
            user = await TelegramUser.objects.aget(chat_id=chat_id)
            tour = await Tour.objects.filter(
                start_time__lt=now, end_time__gt=now
            ).afirst()
            if tour is None:
                tour = await Tour.objects.order_by("-end_time").afirst()
            testings = (
                Testing.objects.filter(tour=tour)
                .order_by("-correct_answers_count", "spent_time")
                .all()
            )
            testings = [test async for test in testings]
            user_id_to_find = user.id
            try:
                current_user_testing = await Testing.objects.filter(
                    tg_user=user, tour=tour
                ).afirst()
                if current_user_testing is None:
                    raise ObjectDoesNotExist
            except ObjectDoesNotExist:
                current_user_score = 0
            else:
                current_user_score = current_user_testing.correct_answers_count

            try:
                index = next(
                    index
                    for index, testing in enumerate(testings, 1)
                    if testing.tg_user_id == user_id_to_find
                )
            except StopIteration:
                index = 0
            testing = [
                {"user": test.tg_user_id, "score": test.correct_answers_count}
                for test in testings[:2]
            ]
            test = {
                "tour_name": tour.name,
                "testings": testing,
                "index": index,
                "current_user_score": current_user_score,
            }
            # print(test)
            return test
        except Exception as e:
            log.error(str(e))
