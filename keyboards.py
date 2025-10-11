# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Создать план"), KeyboardButton(text="📋 Мои планы")],
            [KeyboardButton(text="🧾 Список покупок"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def back_kb_single():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True)

def sex_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мужчина"), KeyboardButton(text="Женщина")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

def goal_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Похудение"), KeyboardButton(text="Набор")],
            [KeyboardButton(text="Рекомпозиция"), KeyboardButton(text="Свой КБЖУ")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

def activity_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Низкая (сидячая)"), KeyboardButton(text="Нижняя средняя")],
            [KeyboardButton(text="Средняя"), KeyboardButton(text="Высокая")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

def meals_count_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="3"), KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

def plans_after_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔁 Показать текущий"), KeyboardButton(text="➕ Создать ещё план")],
            [KeyboardButton(text="🗑 Удалить план"), KeyboardButton(text="◀️ В меню")]
        ], resize_keyboard=True
    )

def plans_menu_kb(plan_names):
    rows = [[KeyboardButton(text=n)] for n in plan_names]
    rows.append([KeyboardButton(text="◀️ В меню"), KeyboardButton(text="🗑 Удалить план")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def shopping_period_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="На 3 дня"), KeyboardButton(text="На неделю")],
            [KeyboardButton(text="На месяц"), KeyboardButton(text="◀️ В меню")]
        ], resize_keyboard=True
    )

def hide_kb():
    return ReplyKeyboardRemove()
