from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Users, MessagesForUsers, Culture, Meet
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging
logger = logging.getLogger(__name__)

router = Router()


class GetUserCode(StatesGroup):
    code = State()


class GetCulture(StatesGroup):
    price = State()
    category = State()


class GetDate(StatesGroup):
    date_input = State()


class Diary(StatesGroup):
    meet_select = State()
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    photo = State()



price_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Бесплатно")],
        [KeyboardButton(text="До 500 ₽")],
        [KeyboardButton(text="До 1000 ₽")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

category_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Музей"), KeyboardButton(text="Парк")],
        [KeyboardButton(text="Покушать"), KeyboardButton(text="На весь день")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Встреча"), KeyboardButton(text="Дата")],
        [KeyboardButton(text="Дневник")],
    ],
    resize_keyboard=True,
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
)

PRICE_MAP = {
    "Бесплатно": (False, False),
    "До 500 ₽": (True, False),
    "До 1000 ₽": (False, True),
}
CATEGORY_MAP = {
    "Музей": "is_museum",
    "Парк": "is_park",
    "Покушать": "is_delicious",
    "На весь день": "is_all_day",
}
DATE_RE = re.compile(r"^(@\w+)-(\d{2}\.\d{2}\.\d{4})$")
DIARY_RE = re.compile(r"^встреча-(@\w+)$", re.IGNORECASE)


@router.message(CommandStart())
async def cmd_start(m: types.Message, state: FSMContext):
    if not m.from_user.username:
        await m.answer("Открой имя пользователя в Telegram и попробуй снова.")
        return
    await m.answer(
            "Привет👋\nМеня зовут Русь, я буду твоим помощником на протяжении всего проекта «Дорога в Россию»🧡\n\n"
            "Напиши, пожалуйста, свой индивидуальный номер\n\n"
            "P.S Он был отправлен тебе в личные сообщения. Если вдруг по каким-то причинам ты его не получил, сообщи об этом @AnnaLastochka20 и возвращайся сюда."
        )
    
    await state.set_state(GetUserCode.code)


# ───────────────────── регистрация по коду ────────────────────
@router.message(GetUserCode.code)
async def process_code(m: types.Message, state: FSMContext, session: AsyncSession):
    code = m.text.strip()
    msgs = (await session.execute(select(MessagesForUsers).where(MessagesForUsers.code == code))).scalars().all()
    if not msgs:
        await m.answer("Код не найден. Свяжитесь с организатором @AnnaLastochka20.")
        return

    if not (await session.execute(select(Users).where(Users.tg_id == m.from_user.id))).scalar_one_or_none():
        session.add(Users(tg_id=m.from_user.id, tg_username=m.from_user.username))
        await session.flush()

    for msg in msgs:
        await m.answer(msg.text_for_message)
    await session.commit()

    await m.answer(
        "<b>1.</b> Познакомьтесь…\n<b>2.</b> Согласуйте встречу за 2 дня.\n<b>3.</b> Используйте меню.",
        parse_mode="HTML", reply_markup=menu_kb)
    await state.clear()


@router.message(F.text.casefold() == "встреча")
async def meet_entry(m: types.Message, state: FSMContext):
    await m.answer(text='И снова привет! Рада, что вы с другом нашли общий язык. Теперь пора выбрать место для вашей встречи. Ответь на вопросы ниже, и я отправлю тебе вариант интересного места для вашего досуга.\n\n'

'Если у тебя два иностранных друга – заполняй разделы «Встреча» и «Дата» последовательно\n\n'

'Время на выбор места и даты – 2 дня с момента отправки этого сообщения.\n\n'

'Важные моменты:\n\n'
'1) Перед тем, как ответить на вопрос бота, узнай мнение своего иностранного друга – ваше решение должно быть совместным;\n'
'2) Если предложенный вариант вас не устроит, просто нажми кнопку «Встреча» в меню ещё раз и выбери другие параметры.\n'
'3) После того, как вы выберете место с помощью бота и согласуете со своим другом дату встречи, выбери в меню «Дата».')
    await m.answer("Выберите бюджет встречи:", reply_markup=price_kb)
    await state.set_state(GetCulture.price)


@router.message(GetCulture.price)
async def meet_price(m: types.Message, state: FSMContext):
    if m.text not in PRICE_MAP:
        await m.answer("Используйте кнопки.")
        return
    await state.update_data(price=m.text)
    await m.answer("Куда бы вы хотели отправиться?", reply_markup=category_kb)
    await state.set_state(GetCulture.category)


@router.message(GetCulture.category)
async def meet_category(m: types.Message, state: FSMContext, session: AsyncSession):
    if m.text not in CATEGORY_MAP:
        await m.answer("Используйте кнопки.")
        return
    data = await state.update_data(category=m.text)
    price_text, cat_text = data["price"], data["category"]
    up_five, up_hundred = PRICE_MAP[price_text]
    cat_field = CATEGORY_MAP[cat_text]

    await m.answer("Подбираю место…", reply_markup=ReplyKeyboardRemove())

    stmt = select(Culture).where(getattr(Culture, cat_field) == True)
    if up_five:
        stmt = stmt.where(Culture.up_five.is_(True))
    if up_hundred:
        stmt = stmt.where(Culture.up_hundred.is_(True))
    place = (await session.execute(stmt.order_by(func.random()).limit(1))).scalar_one_or_none()

    if place:
        text = (
            f"<b>{place.name}</b>\n{place.desc or ''}\n\n"
            f"📍 <b>Адрес:</b> {place.adress}\n"
            f"💰 <b>Бюджет:</b> {price_text}\n"
            f"🏷️ <b>Тип:</b> {cat_text}"
        )
        if place.ya_card and place.ya_card.startswith("AgAC"):
            await m.answer_photo(photo=place.ya_card, caption=text, parse_mode="HTML")
        else:
            await m.answer(text + (f"\n🔗 {place.ya_card}" if place.ya_card else ''), parse_mode="HTML")
    else:
        await m.answer("Не нашлось подходящих мест. Попробуйте другие параметры.")

    await m.answer("После выбора места нажмите «Дата».", reply_markup=menu_kb)
    await state.clear()

# ───────────────────────── «Дата» ─────────────────────────────
@router.message(F.text.casefold() == "дата")
async def date_entry(m: types.Message, state: FSMContext):
    await m.answer(
        "Напиши, пожалуйста, дату вашей встречи, которую вы выбрали со своим другом и укажи свой ID и ник своего иностранного друга в ТГ.\n\n"

        "Формат сообщения:"
        "@никдруга-ДД.ММ.ГГГГ\n\n"
        "Всё без пробелов, через короткое тире)",
        reply_markup=back_kb,
    )
    await state.set_state(GetDate.date_input)


@router.message(GetDate.date_input)
async def save_date(m: types.Message, state: FSMContext, session: AsyncSession):
    if m.text.lower() == "назад":
        await m.answer("Ок, возвращаемся в меню.", reply_markup=menu_kb)
        await state.clear()
        return

    mt = DATE_RE.match(m.text.strip())
    if not mt:
        await m.answer("Неверный формат. Введите, например: @nick-02.07.2025 или нажмите «Назад».")
        logger.warning(f"Invalid date format: {m.text}")
        return

    friend_nick, date_str = mt.groups()

    # Проверка валидности даты
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await m.answer("Некорректная дата. Используйте формат ДД.ММ.ГГГГ, например: @nick-02.07.2025")
        logger.warning(f"Invalid date: {date_str}")
        return

    try:
        # Проверяем, существует ли пользователь по tg_id
        user = (await session.execute(
            select(Users).where(Users.tg_id == m.from_user.id)
        )).scalar_one_or_none()

        if not user:
            await m.answer("Вы не зарегистрированы. Введите /start и код.")
            await state.clear()
            return

        # Проверяем, существует ли встреча
        stmt = select(Meet).where(
            Meet.user_id == user.id,
            Meet.foreigner_tg_name == friend_nick
        )
        meet = (await session.execute(stmt)).scalar_one_or_none()
        if meet:
            meet.date = date_str
        else:
            meet = Meet(
                date=date_str,
                user_id=user.id,
                foreigner_tg_name=friend_nick,
                photo_base64=""
            )
            session.add(meet)
        await session.commit()

        await m.answer("Ответ записан! После встречи выберите «Дневник».", reply_markup=menu_kb)
        await state.clear()

    except IntegrityError as e:
        await m.answer("Ошибка при сохранении данных. Свяжитесь с @AnnaLastochka20.")
        logger.error(f"IntegrityError in save_date: {str(e)}")
        await session.rollback()
    except Exception as e:
        await m.answer("Неизвестная ошибка. Попробуйте позже.")
        logger.error(f"Unexpected error in save_date: {str(e)}")
        await session.rollback()

# ───────────────────────── «Дневник» ──────────────────────────
@router.message(F.text.casefold() == "дневник")
async def diary_entry(m: types.Message, state: FSMContext, session: AsyncSession):
    # Находим пользователя по tg_id
    user = (await session.execute(
        select(Users).where(Users.tg_id == m.from_user.id)
    )).scalar_one_or_none()

    if not user:
        await m.answer("Вы не зарегистрированы. Введите /start и код.")
        return

    # Ищем встречи пользователя без заполненных q1
    stmt = select(Meet).where(Meet.user_id == user.id, Meet.q1.is_(None))
    meets = (await session.execute(stmt)).scalars().all()

    if not meets:
        await m.answer("У вас нет незаполненных дневников. Спасибо!")
        return

    # Создаем инлайн-кнопки для выбора встречи
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"@{x.foreigner_tg_name} ({x.date})", callback_data=f"pick:{x.id}")]
        for x in meets
    ])
    await m.answer("Вот ваши встречи. Выберите, для какой заполнить дневник:", reply_markup=kb)
    await state.set_state(Diary.meet_select)


@router.callback_query(Diary.meet_select, F.data.startswith("pick:"))
async def diary_pick(cb: types.CallbackQuery, state: FSMContext):
    meet_id = int(cb.data.split(":", 1)[1])
    await state.update_data(meet_id=meet_id)
    await cb.message.edit_text("Расскажи, где вы с другом побывали и чем занимались?")
    await state.set_state(Diary.q1)
    await cb.answer()


@router.message(Diary.meet_select)
async def diary_select_by_text(m: types.Message, state: FSMContext, session: AsyncSession):
    match = DIARY_RE.match(m.text.strip())
    if not match:
        await m.answer("Неверный формат строки. Попробуй снова, например: встреча-@nick")
        return
    _, friend_nick = match.groups()

    # Находим пользователя по tg_id
    user = (await session.execute(
        select(Users).where(Users.tg_id == m.from_user.id)
    )).scalar_one_or_none()

    if not user:
        await m.answer("Вы не зарегистрированы. Введите /start и код.")
        return

    # Ищем встречу
    meet = (
        await session.execute(
            select(Meet).where(Meet.user_id == user.id, Meet.foreigner_tg_name == friend_nick)
        )
    ).scalar_one_or_none()
    if not meet:
        await m.answer("Встреча не найдена. Проверь ник.")
        return
    await state.update_data(meet_id=meet.id)
    await m.answer("Расскажи, где вы с другом побывали и чем занимались?")
    await state.set_state(Diary.q1)


async def _save_q(m: types.Message, state: FSMContext, session: AsyncSession, field: str, next_state: Optional[State], next_q: str):
    data = await state.get_data()
    meet = await session.get(Meet, data["meet_id"])
    setattr(meet, field, m.text)
    await session.commit()

    if next_state:
        await m.answer(next_q)
        await state.set_state(next_state)
    else:
        await m.answer("Отправь сюда фотографию с вашей встречи.")
        await state.set_state(Diary.photo)


@router.message(Diary.q1)
async def diary_q1(m: types.Message, state: FSMContext, session: AsyncSession):
    await _save_q(m, state, session, "q1", Diary.q2, "Что тебе понравилось?")


@router.message(Diary.q2)
async def diary_q2(m: types.Message, state: FSMContext, session: AsyncSession):
    await _save_q(m, state, session, "q2", Diary.q3, "Возникали ли языковые или культурные трудности?")


@router.message(Diary.q3)
async def diary_q3(m: types.Message, state: FSMContext, session: AsyncSession):
    await _save_q(m, state, session, "q3", Diary.q4, "Как можно помочь иностранным студентам?")


@router.message(Diary.q4)
async def diary_q4(m: types.Message, state: FSMContext, session: AsyncSession):
    await _save_q(m, state, session, "q4", Diary.q5, "Есть ли ещё что-то, чем бы ты хотел поделиться?")


@router.message(Diary.q5)
async def diary_q5(m: types.Message, state: FSMContext, session: AsyncSession):
    await _save_q(m, state, session, "q5", None, "Отправь фото.")


@router.message(Diary.photo, F.photo)
async def diary_photo(m: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    meet = await session.get(Meet, data["meet_id"])
    # сохраняем file_id как текст; при желании можно скачивать и хранить base64
    meet.photo_base64 = m.photo[-1].file_id
    await session.commit()

    await m.answer(
        "Спасибо за отзыв! Мы были рады видеть тебя в проекте «Дорога в Россию».\n"
        "Не забывай следить за новостями: https://vk.com/roadtorussia",
        reply_markup=menu_kb,
    )
    await state.clear()