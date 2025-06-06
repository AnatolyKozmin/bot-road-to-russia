# -*- coding: utf-8 -*-
"""
Telegram bot – проект «Дорога в Россию»
======================================

Функционал:
-----------
1. **Регистрация** по персональному коду (`/start`).
2. **Встреча** – подбор места (бюджет → категория) и рекомендация.
3. **Дата** – пользователь присылает строку вида `RTR0001-@nickname-12.06.2025`,
   создаём/обновляем запись `Meet` (поля могут дописываться позднее).
4. **Дневник** – последовательный опрос после встречи + фото; ответы дозаписываются
   в существующий `Meet` (по пользователю и нику иностранца). Если открытых
   встреч несколько – отдаём кнопки выбора.

SQLAlchemy модели
-----------------
* Используется схема из `db.models` выше: `Culture`, `Users`, `MessagesForUsers`, `Meet`.
* Для `Culture` есть булевые флаги `up_five`, `up_hundred`, `is_museum`, `is_park`,
  `is_delicious`, `is_all_day`.

Aiogram
-------
* Версия 3.x (Router‑based).
* FSM: 4 группы состояний.
    - `GetUserCode`
    - `GetCulture`   (price → category)
    - `GetDate`      (один шаг: строка с датой)
    - `Diary`        (meet_select → q1…q5 → photo)

NB: минимальная обработка ошибок/валидации – при желании можно усилить.
"""

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
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Users, MessagesForUsers, Culture, Meet

router = Router()

# ────────────────────────── FSM ────────────────────────────────
class GetUserCode(StatesGroup):
    code = State()


class GetCulture(StatesGroup):
    price = State()
    category = State()


class GetDate(StatesGroup):
    date_input = State()


class Diary(StatesGroup):
    meet_select = State()   # выбор встречи, если их >1
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    photo = State()


# ─────────────────────── клавиатуры ───────────────────────────
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

# ───────────────────────── helpers ────────────────────────────
PRICE_MAP = {
    "Бесплатно": (False, False),       # up_five=False & up_hundred=False
    "До 500 ₽": (True, False),         # up_five=True
    "До 1000 ₽": (False, True),        # up_hundred=True
}

CATEGORY_MAP = {
    "Музей": "is_museum",
    "Парк": "is_park",
    "Покушать": "is_delicious",
    "На весь день": "is_all_day",
}

DATE_RE = re.compile(r"^(RTR\d{4})-(@\w+)-(\d{2}\.\d{2}\.\d{4})$")
DIARY_RE = re.compile(r"^встреча-(RTR\d{4})-(@\w+)$", re.IGNORECASE)

# ───────────────────────── /start ─────────────────────────────
@router.message(CommandStart())
async def cmd_start(m: types.Message, state: FSMContext):
    if m.from_user.username is None:
        await m.answer("Пожалуйста, открой имя пользователя в Telegram и попробуй снова.")
        return

    await m.answer(
        "Привет👋\nМеня зовут Русь, я буду твоим помощником в проекте «Дорога в Россию».\n\n"
        "Напиши, пожалуйста, свой индивидуальный номер."
    )
    await state.set_state(GetUserCode.code)


# ───────────────────── регистрация по коду ────────────────────
@router.message(GetUserCode.code)
async def process_code(m: types.Message, state: FSMContext, session: AsyncSession):
    code = m.text.strip()
    res = await session.execute(select(MessagesForUsers).where(MessagesForUsers.code == code))
    msgs = res.scalars().all()
    if not msgs:
        await m.answer("Код не найден. Свяжитесь с организатором @AnnaLastochka20.")
        return

    usr = (await session.execute(select(Users).where(Users.tg_id == m.from_user.id))).scalar_one_or_none()
    if not usr:
        session.add(Users(tg_id=m.from_user.id, tg_username=m.from_user.username))
        await session.flush()

    for msg in msgs:
        await m.answer(msg.text_for_message)

    await session.commit()

    await m.answer(
        "<b>1.</b> Познакомьтесь со своим другом.\n"
        "<b>2.</b> Согласуйте встречу в течение 2 дней.\n"
        "<b>3.</b> Используйте меню ниже для следующих шагов.",
        parse_mode="HTML",
        reply_markup=menu_kb,
    )
    await state.clear()

# ───────────────────────── «Встреча» ──────────────────────────
@router.message(F.text.casefold() == "встреча")
async def meet_entry(m: types.Message, state: FSMContext):
    await m.answer(
        "Выберите бюджет встречи:",
        reply_markup=price_kb,
    )
    await state.set_state(GetCulture.price)


@router.message(GetCulture.price)
async def meet_price(m: types.Message, state: FSMContext):
    if m.text not in PRICE_MAP:
        await m.answer("Пожалуйста, выберите вариант из клавиатуры.")
        return
    await state.update_data(price=m.text)
    await m.answer("Куда бы вы хотели отправиться?", reply_markup=category_kb)
    await state.set_state(GetCulture.category)


@router.message(GetCulture.category)
async def meet_category(m: types.Message, state: FSMContext, session: AsyncSession):
    if m.text not in CATEGORY_MAP:
        await m.answer("Выберите вариант из клавиатуры.")
        return

    data = await state.update_data(category=m.text)
    price_text, cat_text = data["price"], data["category"]

    up_five, up_hundred = PRICE_MAP[price_text]
    cat_field = CATEGORY_MAP[cat_text]

    await m.answer("Подбираю место…", reply_markup=ReplyKeyboardRemove())

    stmt = (
        select(Culture)
        .where(getattr(Culture, cat_field) == True)
        .where(Culture.up_five == up_five if up_five else True)
        .where(Culture.up_hundred == up_hundred if up_hundred else True)
        .order_by(func.random())
        .limit(1)
    )
    place = (await session.execute(stmt)).scalar_one_or_none()

    if place:
        text = (
            f"<b>{place.name}</b>\n"
            f"{place.desc or ''}\n\n"
            f"📍 <b>Адрес:</b> {place.adress}\n"
            f"💰 <b>Бюджет:</b> {price_text}\n"
            f"🏷️ <b>Тип:</b> {cat_text}\n"
            f"{'🔗 ' + place.site if place.site else ''}"
        )
        if place.ya_card:
            await m.answer_photo(photo=place.ya_card, caption=text, parse_mode="HTML")
        else:
            await m.answer(text, parse_mode="HTML")
    else:
        await m.answer("Не нашлось подходящих мест. Попробуйте другие параметры.")

    await m.answer(
        "Как только выберете удобную дату, нажмите «Дата».\n\n"
        "Напоминаю, что дату нужно выбрать в течение двух дней.",
        reply_markup=menu_kb,
    )
    await state.clear()

# ───────────────────────── «Дата» ─────────────────────────────
@router.message(F.text.casefold() == "дата")
async def date_entry(m: types.Message, state: FSMContext):
    await m.answer(
        "Напиши дату в формате:\nRTR0001-@nick-ДД.ММ.ГГГГ",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(GetDate.date_input)


@router.message(GetDate.date_input)
async def save_date(m: types.Message, state: FSMContext, session: AsyncSession):
    match = DATE_RE.match(m.text.strip())
    if not match:
        await m.answer("Неверный формат. Проверь пример и попробуй снова.")
        return

    user_code, friend_nick, date_str = match.groups()
    try:
        meet_date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await m.answer("Неверная дата. Используйте ДД.ММ.ГГГГ.")
        return

    # либо обновляем существующую, либо создаём новую запись Meet
    stmt = select(Meet).where(
        Meet.user_id == m.from_user.id,
        Meet.foreigner_tg_name == friend_nick,
    )
    res = await session.execute(stmt)
    meet = res.scalar_one_or_none()
    if meet:
        meet.date = date_str
    else:
        meet = Meet(date=date_str, user_id=m.from_user.id, foreigner_tg_name=friend_nick)
        session.add(meet)

    await session.commit()

    await m.answer(
        "Ответ записан! Не забудьте сделать совместную фотографию).\n\n"
        "После встречи выберите пункт «Дневник» в меню.",
        reply_markup=menu_kb,
    )
    await state.clear()

# ───────────────────────── «Дневник» ──────────────────────────
@router.message(F.text.casefold() == "дневник")
async def diary_entry(m: types.Message, state: FSMContext, session: AsyncSession):
    # ищем встречи пользователя без заполненных q1
    stmt = select(Meet).where(Meet.user_id == m.from_user.id, Meet.q1.is_(None))
    meets = (await session.execute(stmt)).scalars().all()

    if not meets:
        await m.answer("У вас нет незаполненных дневников. Спасибо!")
        return

    if len(meets) == 1:
        await state.update_data(meet_id=meets[0].id)
        await m.answer("Напиши строку вида: встреча-RTR0001-@nick")
        await state.set_state(Diary.meet_select)
    else:
        # отдаём инлайн‑кнопки
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"@{x.foreigner_tg_name}", callback_data=f"pick:{x.id}")]
            for x in meets
        ])
        await m.answer("У вас несколько встреч. Выберите, для какой заполнить дневник:", reply_markup=kb)
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
        await m.answer("Неверный формат строки. Попробуй снова.")
        return
    _, friend_nick = match.groups()
    meet = (
        await session.execute(select(Meet).where(Meet.user_id == m.from_user.id, Meet.foreigner_tg_name == friend_nick))
    ).scalar_one_or_none()
    if not meet:
        await m.answer("Встреча не найдена. Проверь ник.")
        return
    await state.update_data(meet_id=meet.id)
    await m.answer("Расскажи, где вы с другом побывали и чем занимались?")
    await state.set_state(Diary.q1)

# ---- последовательные вопросы ----
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


# ───────────────────────── End ────────────────────────────────











