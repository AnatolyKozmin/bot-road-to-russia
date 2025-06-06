from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command, or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Users
from db.models import MessagesForUsers

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.engine import session_maker


user_router = Router()

class GetUserCode(StatesGroup):
    code = State()

@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    if message.from_user.username is None:
        await message.answer(
            "Привет, у тебя закрыто имя пользователя в Telegram. Открой его в настройках и попробуй снова."
        )
    else:
        await message.answer(
            "Привет👋\nМеня зовут Русь, я буду твоим помощником на протяжении всего проекта «Дорога в Россию»🧡\n\n"
            "Напиши, пожалуйста, свой индивидуальный номер\n\n"
            "P.S Он был отправлен тебе в личные сообщения. Если вдруг по каким-то причинам ты его не получил, сообщи об этом @AnnaLastochka20 и возвращайся сюда."
        )
        await state.set_state(GetUserCode.code)

@user_router.message(GetUserCode.code)
async def process_code(message: types.Message, state: FSMContext, session: AsyncSession):
    code = message.text.strip()
    result = await session.execute(
        select(MessagesForUsers).where(MessagesForUsers.code == code)
    )
    messages = result.scalars().all()

    if not messages:
        await message.answer("Код не найден. Попробуйте еще раз или обратитесь к организатору @AnnaLastochka20.")
        return

    # Сохраняем пользователя, если его нет
    user_result = await session.execute(
        select(Users).where(Users.tg_id == message.from_user.id)
    )
    user_obj = user_result.scalar_one_or_none()
    if not user_obj:
        user = Users(
            tg_id=message.from_user.id,
            tg_username=message.from_user.username
        )
        session.add(user)
        await session.commit()

    # Выводим все найденные сообщения (каждое — отдельным сообщением)
    for msg in messages:
        await message.answer(msg.text_for_message)

    # Форматированное сообщение и кнопка "Встреча" — только один раз
    formatted_text = (
        "<b>1. Сейчас тебе нужно сделать следующие шаги:</b>\n\n"
        "Написать в личные сообщения своему другу следующее сообщение:\n\n"
        "<i>«Привет! Я – твой русский друг из проекта «Дорога в Россию». Меня зовут <b>имя</b>, я учусь в <b>каком университете</b> на факультете <b>направление</b>. Давай знакомиться) Подскажи, <b>один из вопросов ниже</b>.\n\n"
        "2. Познакомиться со своим другом онлайн, задав следующие вопросы:</i>\n"
        "• Как тебя зовут?\n"
        "• Из какой страны ты приехал и как давно?\n"
        "• Какие языки ты знаешь?\n"
        "• В какой университет ты собираешься поступать и на какое направление?\n"
        "• Какие у тебя хобби?\n"
        "• Почему ты выбрал Россию для обучения?\n\n"
        "<i>Список вопросов является примерным и включает в себя основные моменты, необходимые для знакомства на первом этапе.</i>\n\n"
        "Предложить своему иностранному другу увидеться вживую и познакомиться поближе.\n\n"
        "<b>На выполнение этого этапа у тебя есть 2 дня с момента отправки этого сообщения.</b>\n\n"
        "Как только вы со своим другом наладите первичный контакт и примите решение о встрече, возвращайся сюда и выбирай в меню «Встреча».\n\n"
        "Я помогу вам подобрать интересное место для прогулки в зависимости от ваших интересов (парк/музей/выставка/гастро места/иное) и бюджета (бесплатно/до 500 рублей/1000 рублей)."
    )
    meet_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Встреча")]],
        resize_keyboard=True
    )
    await message.answer(formatted_text, parse_mode="HTML", reply_markup=meet_kb)
    await state.clear()

    
@user_router.message(F.text == "Встреча")
async def meet_handler(message: types.Message):
    await message.answer(
        "У тебя есть 2 дня на то, чтобы наладить контакт с момента ввода кода!\n\n"
        "После 2 дней здесь появятся варианты для встречи, которые мы собрали специально для тебя.\n\n" \
        "Если вдруг что-то идёт не так, то нажми на  /start и попробуй снова"
    )