# telegram_food_bot.py
# Требует: aiogram==3.4.1, aiosqlite
# Запуск: убедитесь, что переменная окружения BOT_TOKEN установлена, затем:
# python telegram_food_bot.py

import os
import json
import math
import random
import asyncio
from typing import Dict, Any, List, Optional

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

# -------------------- Настройки --------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не установлена (BOT_TOKEN)")

# Создаём Bot с дефолтными свойствами (parse_mode)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher(storage=MemoryStorage())

DB_PATH = "nutrition_bot.db"

# -------------------- FSM --------------------
class Form(StatesGroup):
    sex = State()
    goal = State()
    weight = State()
    height = State()
    age = State()
    activity = State()
    meals_count = State()
    custom_kbju = State()
    plan_name = State()
    shopping_period = State()
    delete_plan = State()

# -------------------- Продукты (по категориям) --------------------
# Можно расширить или вынести в products.py
PROTEINS = [
    {"name": "Куриная грудка", "protein": 23, "fat": 1.9, "carbs": 0, "kcal": 110},
    {"name": "Индейка", "protein": 22, "fat": 2, "carbs": 0, "kcal": 120},
    {"name": "Яйцо", "protein": 13, "fat": 11, "carbs": 1, "kcal": 155},
    {"name": "Творог 5%", "protein": 16, "fat": 5, "carbs": 3, "kcal": 120},
    {"name": "Говядина (постная)", "protein": 20, "fat": 8, "carbs": 0, "kcal": 190},
    {"name": "Сёмга", "protein": 20, "fat": 12, "carbs": 0, "kcal": 210},
]

CARBS = [
    {"name": "Овсянка", "protein": 11, "fat": 6, "carbs": 60, "kcal": 350},
    {"name": "Рис (сырой)", "protein": 7, "fat": 0.6, "carbs": 75, "kcal": 340},
    {"name": "Гречка", "protein": 13, "fat": 3.4, "carbs": 72, "kcal": 329},
    {"name": "Картофель", "protein": 2, "fat": 0.1, "carbs": 17, "kcal": 77},
    {"name": "Макароны", "protein": 12, "fat": 1.5, "carbs": 72, "kcal": 350},
]

FATS = [
    {"name": "Оливковое масло", "protein": 0, "fat": 100, "carbs": 0, "kcal": 900},
    {"name": "Грецкие орехи", "protein": 15, "fat": 65, "carbs": 10, "kcal": 650},
    {"name": "Арахис", "protein": 25, "fat": 50, "carbs": 10, "kcal": 570},
    {"name": "Авокадо", "protein": 2, "fat": 15, "carbs": 9, "kcal": 160},
]

VEGGIES = [
    {"name": "Брокколи", "protein": 3, "fat": 0.4, "carbs": 7, "kcal": 35},
    {"name": "Огурец", "protein": 0.8, "fat": 0.1, "carbs": 3, "kcal": 15},
    {"name": "Помидор", "protein": 0.9, "fat": 0.2, "carbs": 3.5, "kcal": 20},
    {"name": "Морковь", "protein": 0.9, "fat": 0.2, "carbs": 10, "kcal": 41},
    {"name": "Салат (микс)", "protein": 1.2, "fat": 0.2, "carbs": 2, "kcal": 15},
]

MEAL_NAMES = ["Завтрак", "Перекус 1", "Обед", "Перекус 2", "Ужин"]

# -------------------- БД (SQLite) --------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                kcal INTEGER NOT NULL,
                protein REAL NOT NULL,
                fat REAL NOT NULL,
                carbs REAL NOT NULL,
                meals_count INTEGER NOT NULL,
                daily_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_plan_db(user_id: int, name: str, kcal: int, p: float, f: float, c: float, meals_count: int, daily: List[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO plans (user_id,name,kcal,protein,fat,carbs,meals_count,daily_json) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, name, kcal, p, f, c, meals_count, json.dumps(daily, ensure_ascii=False))
        )
        await db.commit()

async def get_user_plans(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id,name,kcal,protein,fat,carbs,meals_count,daily_json FROM plans WHERE user_id=? ORDER BY created_at", (user_id,))
        rows = await cur.fetchall()
        await cur.close()
    plans = []
    for r in rows:
        plans.append({
            "id": r[0],
            "name": r[1],
            "kcal": r[2],
            "protein": r[3],
            "fat": r[4],
            "carbs": r[5],
            "meals_count": r[6],
            "daily": json.loads(r[7])
        })
    return plans

async def delete_plan_db(user_id: int, name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM plans WHERE user_id=? AND name=?", (user_id, name))
        await db.commit()
        affected = cur.rowcount
        await cur.close()
    return affected > 0

async def get_plan_by_name(user_id: int, name: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id,name,kcal,protein,fat,carbs,meals_count,daily_json FROM plans WHERE user_id=? AND name=?", (user_id, name))
        row = await cur.fetchone()
        await cur.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "kcal": row[2],
        "protein": row[3],
        "fat": row[4],
        "carbs": row[5],
        "meals_count": row[6],
        "daily": json.loads(row[7])
    }

# -------------------- Формулы и генерация меню --------------------
def calc_bmr_mifflin(weight: float, height: float, age: int, sex: str) -> float:
    if sex == "Мужчина":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def activity_multiplier(choice: str) -> float:
    mapping = {
        "Низкая (сидячая)": 1.2,
        "Нижняя средняя": 1.375,
        "Средняя": 1.55,
        "Высокая": 1.725
    }
    return mapping.get(choice, 1.2)

def grams_for_target_macro(item_macro_per100: float, target_macro: float) -> float:
    if item_macro_per100 <= 0:
        return 0.0
    return (target_macro / item_macro_per100) * 100.0

def generate_meal_plan(total_kcal: int, total_p: float, total_f: float, total_c: float, meals_count: int) -> List[dict]:
    meal_plan = []
    p_per = total_p / meals_count
    f_per = total_f / meals_count
    c_per = total_c / meals_count

    for i in range(meals_count):
        protein = random.choice(PROTEINS)
        carb = random.choice(CARBS)
        veg = random.choice(VEGGIES)
        fat = random.choice(FATS) if random.random() < 0.6 else None

        prot_g = grams_for_target_macro(protein["protein"], p_per)
        carb_g = grams_for_target_macro(carb["carbs"], c_per)
        veg_g = 100
        fat_g = grams_for_target_macro(fat["fat"], f_per) if fat else 0.0

        prot_g = max(50, min(prot_g, 300))
        carb_g = max(30, min(carb_g, 300))
        fat_g = max(0, min(fat_g, 80))
        veg_g = max(50, min(veg_g, 300))

        def make_entry(prod, g):
            return {
                "name": prod["name"],
                "grams": int(round(g)),
                "protein": round(prod.get("protein", 0) * g / 100, 1),
                "fat": round(prod.get("fat", 0) * g / 100, 1),
                "carbs": round(prod.get("carbs", 0) * g / 100, 1),
                "kcal": int(round(prod.get("kcal", 0) * g / 100))
            }

        items = [make_entry(protein, prot_g), make_entry(carb, carb_g), make_entry(veg, veg_g)]
        if fat:
            items.append(make_entry(fat, fat_g))

        totals = {"kcal": 0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        for it in items:
            totals["kcal"] += it["kcal"]
            totals["protein"] += it["protein"]
            totals["fat"] += it["fat"]
            totals["carbs"] += it["carbs"]

        meal_plan.append({
            "meal_name": MEAL_NAMES[i] if i < len(MEAL_NAMES) else f"Приём {i+1}",
            "items": items,
            "totals": totals
        })

    return meal_plan

def format_daily_markdown(meal_plan: List[dict]) -> str:
    lines = ["*📅 План на день*"]
    totals = {"kcal": 0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for meal in meal_plan:
        lines.append(f"\n*🍽 {meal['meal_name']}* — _~{meal['totals']['kcal']} ккал_")
        for it in meal["items"]:
            lines.append(f"• {it['name']} — {it['grams']} г (Б {it['protein']} г, Ж {it['fat']} г, У {it['carbs']} г)")
            totals["kcal"] += it["kcal"]
            totals["protein"] += it["protein"]
            totals["fat"] += it["fat"]
            totals["carbs"] += it["carbs"]
    lines.append(f"\n*📊 Итого за день:* _{round(totals['kcal'])} ккал — Б {round(totals['protein'],1)} г / Ж {round(totals['fat'],1)} г / У {round(totals['carbs'],1)} г_")
    return "\n".join(lines)

def aggregate_shopping(meal_plan: List[dict], days: int) -> Dict[str, float]:
    agg: Dict[str, float] = {}
    for meal in meal_plan:
        for it in meal["items"]:
            name = it["name"]
            grams = it["grams"] * days
            agg[name] = agg.get(name, 0.0) + grams
    return agg

def format_shopping_list(agg: Dict[str, float]) -> str:
    if not agg:
        return "Список пуст."
    lines = ["*🛒 Список покупок*"]
    for name, grams in sorted(agg.items(), key=lambda x: -x[1]):
        if grams >= 1000:
            lines.append(f"• {name} — {grams/1000:.2f} кг ({int(grams)} г)")
        else:
            lines.append(f"• {name} — {int(grams)} г")
    return "\n".join(lines)

# -------------------- Клавиатуры --------------------
def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Создать план"), KeyboardButton(text="📋 Мои планы")],
            [KeyboardButton(text="🧾 Список покупок"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def sex_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мужчина"), KeyboardButton(text="Женщина")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def goal_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Похудение"), KeyboardButton(text="Набор")],
            [KeyboardButton(text="Рекомпозиция"), KeyboardButton(text="Свой КБЖУ")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def activity_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Низкая (сидячая)"), KeyboardButton(text="Нижняя средняя")],
            [KeyboardButton(text="Средняя"), KeyboardButton(text="Высокая")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def meals_count_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="3"), KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def plans_menu_kb(plan_names: List[str]):
    rows = [[KeyboardButton(text=n)] for n in plan_names]
    rows.append([KeyboardButton(text="◀️ В меню"), KeyboardButton(text="🗑 Удалить план")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def plans_after_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔁 Показать текущий"), KeyboardButton(text="➕ Создать ещё план")],
            [KeyboardButton(text="🗑 Удалить план"), KeyboardButton(text="◀️ В меню")]
        ],
        resize_keyboard=True
    )

def shopping_period_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="На 3 дня"), KeyboardButton(text="На неделю")],
            [KeyboardButton(text="На месяц"), KeyboardButton(text="◀️ В меню")]
        ],
        resize_keyboard=True
    )

# -------------------- Обработчики --------------------
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await init_db()
    await state.clear()
    await message.answer("Привет! Я помогу составить план питания и список покупок.", reply_markup=main_menu_kb())

@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer("Используй меню:\n• 🆕 Создать план\n• 📋 Мои планы\n• 🧾 Список покупок\nВ любой момент — '⬅️ Назад'.")

# --- Create plan flow ---
@dp.message(F.text == "🆕 Создать план")
async def start_create_plan(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.sex)
    await message.answer("Выберите пол:", reply_markup=sex_kb())

@dp.message((F.text == "Мужчина") | (F.text == "Женщина"), StateFilter(Form.sex))
async def sex_chosen(message: Message, state: FSMContext):
    await state.update_data(sex=message.text)
    await state.set_state(Form.goal)
    await message.answer("Выберите цель:", reply_markup=goal_kb())

@dp.message(StateFilter(Form.goal))
async def goal_chosen(message: Message, state: FSMContext):
    text = message.text.strip()
    allowed = ["Похудение", "Набор", "Рекомпозиция", "Свой КБЖУ", "⬅️ Назад"]
    if text not in allowed:
        await message.answer("Пожалуйста, выберите кнопку.", reply_markup=goal_kb())
        return
    await state.update_data(goal=text)
    if text == "Свой КБЖУ":
        await state.set_state(Form.custom_kbju)
        await message.answer("Введи свои КБЖУ: калории белки жиры углеводы (пример: 2000 180 80 140).", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))
        return
    await state.set_state(Form.weight)
    await message.answer("Введите вес в кг (пример: 75.5):", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))

@dp.message(StateFilter(Form.custom_kbju))
async def custom_kbju_input(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 4:
        await message.answer("Формат: 2000 180 80 140")
        return
    try:
        kcal, p, f, c = map(float, parts)
    except:
        await message.answer("Неверные числа.")
        return
    await state.update_data(custom_kbju={"kcal": int(kcal), "protein": round(p,1), "fat": round(f,1), "carbs": round(c,1)})
    await state.set_state(Form.meals_count)
    await message.answer("Сколько приёмов пищи в день (3-5)?", reply_markup=meals_count_kb())

@dp.message(StateFilter(Form.weight))
async def weight_input(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", "."))
    except:
        await message.answer("Некорректный вес.")
        return
    await state.update_data(weight=w)
    await state.set_state(Form.height)
    await message.answer("Введите рост в см (пример: 178):", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))

@dp.message(StateFilter(Form.height))
async def height_input(message: Message, state: FSMContext):
    try:
        h = float(message.text.replace(",", "."))
    except:
        await message.answer("Некорректный рост.")
        return
    await state.update_data(height=h)
    await state.set_state(Form.age)
    await message.answer("Введите возраст (лет):", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))

@dp.message(StateFilter(Form.age))
async def age_input(message: Message, state: FSMContext):
    try:
        a = int(message.text.strip())
    except:
        await message.answer("Некорректный возраст.")
        return
    await state.update_data(age=a)
    await state.set_state(Form.activity)
    await message.answer("Выберите уровень активности:", reply_markup=activity_kb())

@dp.message(StateFilter(Form.activity))
async def activity_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if text not in ["Низкая (сидячая)", "Нижняя средняя", "Средняя", "Высокая", "⬅️ Назад"]:
        await message.answer("Пожалуйста, выберите кнопку.", reply_markup=activity_kb())
        return
    if text == "⬅️ Назад":
        await state.set_state(Form.age)
        await message.answer("Вернитесь: введите возраст.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))
        return
    await state.update_data(activity=text)
    await state.set_state(Form.meals_count)
    await message.answer("Сколько приёмов пищи в день (3-5)?", reply_markup=meals_count_kb())

@dp.message(StateFilter(Form.meals_count))
async def meals_count_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "⬅️ Назад":
        await state.set_state(Form.activity)
        await message.answer("Выберите уровень активности:", reply_markup=activity_kb())
        return
    try:
        mc = int(text)
        if mc < 3 or mc > 5:
            raise ValueError
    except:
        await message.answer("Выберите 3, 4 или 5.", reply_markup=meals_count_kb())
        return
    await state.update_data(meals_count=mc)

    data = await state.get_data()
    goal = data.get("goal")

    if goal == "Свой КБЖУ":
        kbju = data.get("custom_kbju")
        kcal = kbju["kcal"]; p = kbju["protein"]; f = kbju["fat"]; c = kbju["carbs"]
    else:
        sex = data.get("sex"); weight = data.get("weight"); height = data.get("height"); age = data.get("age"); activity = data.get("activity")
        bmr = calc_bmr_mifflin(weight, height, age, sex)
        tdee = bmr * activity_multiplier(activity)
        if goal == "Похудение":
            kcal = round(tdee * 0.85)
            p = round(weight * 2.0, 1)
            f = round(weight * 1.0, 1)
            c = round((kcal - p*4 - f*9)/4, 1)
        elif goal == "Набор":
            kcal = round(tdee * 1.15)
            p = round(weight * 2.0, 1)
            f = round(weight * 1.2, 1)
            c = round((kcal - p*4 - f*9)/4, 1)
        elif goal == "Рекомпозиция":
            if sex == "Мужчина":
                p = round(weight * 2.2, 1)
                f = round(weight * 0.8, 1)
                c = round(weight * 2.2, 1)
            else:
                p = round(weight * 1.5, 1)
                f = round(weight * 1.0, 1)
                c = round(weight * 2.2, 1)
            kcal = round(p*4 + f*9 + c*4)
        else:
            kcal = round(tdee)
            p = round(weight * 2.0, 1)
            f = round(weight * 1.0, 1)
            c = round((kcal - p*4 - f*9)/4, 1)

    meals_count = data.get("meals_count")
    daily = generate_meal_plan(kcal, p, f, c, meals_count)
    md = format_daily_markdown(daily)

    await state.update_data(calc_result={"kcal": kcal, "protein": p, "fat": f, "carbs": c, "meals_count": meals_count, "daily": daily})
    await state.set_state(Form.plan_name)
    await message.answer(f"Готово — предложенный план:\n*Калории:* {kcal} ккал\n*Белки:* {p} г  *Жиры:* {f} г  *Углеводы:* {c} г", reply_markup=ReplyKeyboardRemove())
    await message.answer(md)
    await message.answer("Введите имя для сохранения плана или отправьте 'Нет' чтобы не сохранять.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True))

@dp.message(StateFilter(Form.plan_name))
async def plan_name_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "⬅️ Назад":
        await state.set_state(Form.meals_count)
        await message.answer("Сколько приёмов в день (3-5)?", reply_markup=meals_count_kb())
        return
    data = await state.get_data()
    calc = data.get("calc_result")
    if not calc:
        await message.answer("Нет расчёта.", reply_markup=main_menu_kb())
        await state.clear()
        return
    if text.lower() == "нет":
        await message.answer("ОК, не сохраняем.", reply_markup=main_menu_kb())
        await state.clear()
        return
    await save_plan_db(message.from_user.id, text, int(calc["kcal"]), float(calc["protein"]), float(calc["fat"]), float(calc["carbs"]), int(calc["meals_count"]), calc["daily"])
    await message.answer(f"План '*{text}*' сохранён.", parse_mode="Markdown", reply_markup=plans_after_kb())
    await state.clear()

# -------------------- Управление планами --------------------
@dp.message(F.text == "📋 Мои планы")
async def my_plans(message: Message):
    plans = await get_user_plans(message.from_user.id)
    if not plans:
        await message.answer("У вас нет планов. Создайте через '🆕 Создать план'.", reply_markup=main_menu_kb())
        return
    names = [p["name"] for p in plans]
    await message.answer("Ваши планы (нажмите на имя, чтобы открыть):\n" + "\n".join(f"- {n}" for n in names), reply_markup=plans_menu_kb(names))

@dp.message(F.text == "◀️ В меню")
async def back_menu(message: Message):
    await message.answer("Возврат в меню.", reply_markup=main_menu_kb())

@dp.message(F.text == "🔁 Показать текущий")
async def show_current(message: Message):
    plans = await get_user_plans(message.from_user.id)
    if not plans:
        await message.answer("Нет сохранённых планов.", reply_markup=main_menu_kb())
        return
    plan = plans[-1]
    md = format_daily_markdown(plan["daily"])
    await message.answer(f"Активный (последний) план: *{plan['name']}*\nКкал: {plan['kcal']}  Б: {plan['protein']}  Ж: {plan['fat']}  У: {plan['carbs']}", parse_mode="Markdown", reply_markup=plans_after_kb())
    await message.answer(md)

@dp.message(F.text == "➕ Создать ещё план")
async def create_more(message: Message):
    await start_create_plan(message, dp.current_state(user=message.from_user.id))

@dp.message(F.text == "🗑 Удалить план")
async def delete_plan_prompt(message: Message):
    await message.answer("Отправьте точное имя плана для удаления или 'Отмена'.", reply_markup=ReplyKeyboardRemove())
    await dp.current_state(user=message.from_user.id).set_state(Form.delete_plan)

@dp.message(StateFilter(Form.delete_plan))
async def delete_plan_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() in ("отмена", "cancel"):
        await message.answer("Отмена.", reply_markup=main_menu_kb())
        await state.clear()
        return
    ok = await delete_plan_db(message.from_user.id, text)
    if ok:
        await message.answer(f"План '{text}' удалён.", reply_markup=main_menu_kb())
    else:
        await message.answer("План не найден.", reply_markup=main_menu_kb())
    await state.clear()

# -------------------- Список покупок --------------------
@dp.message(F.text == "🧾 Список покупок")
async def shopping_start(message: Message, state: FSMContext):
    plans = await get_user_plans(message.from_user.id)
    if not plans:
        await message.answer("У вас нет планов. Создайте план.", reply_markup=main_menu_kb())
        return
    current = plans[-1]
    await state.update_data(shopping_plan_name=current["name"])
    await state.set_state(Form.shopping_period)
    await message.answer(f"Выбран план: *{current['name']}*.\nВыберите период:", parse_mode="Markdown", reply_markup=shopping_period_kb())

@dp.message(StateFilter(Form.shopping_period))
async def shopping_period_chosen(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "◀️ В меню":
        await state.clear()
        await message.answer("Отмена.", reply_markup=main_menu_kb())
        return
    days_map = {"На 3 дня": 3, "На неделю": 7, "На месяц": 30}
    if text not in days_map:
        await message.answer("Выберите кнопку.", reply_markup=shopping_period_kb())
        return
    days = days_map[text]
    data = await state.get_data()
    plan_name = data.get("shopping_plan_name")
    plan = await get_plan_by_name(message.from_user.id, plan_name)
    if not plan:
        await message.answer("План не найден.", reply_markup=main_menu_kb())
        await state.clear()
        return
    daily = plan["daily"]
    agg = aggregate_shopping(daily, days)
    shopping_text = format_shopping_list(agg)
    await message.answer(f"🛒 *Список покупок* для плана *{plan_name}* на *{days}* дней:\n\n{shopping_text}", parse_mode="Markdown", reply_markup=main_menu_kb())
    await state.clear()

# -------------------- Кнопка "⬅️ Назад" --------------------
@dp.message(StateFilter("*"), F.text == "⬅️ Назад")
async def go_back(message: Message, state: FSMContext):
    # Для простоты — очищаем состояние и возвращаем в меню
    await state.clear()
    await message.answer("Возврат. Вы в меню.", reply_markup=main_menu_kb())

# -------------------- Catch-all (открытие плана по имени) --------------------
@dp.message()
async def fallback(message: Message, state: FSMContext):
    name = message.text.strip()
    plan = await get_plan_by_name(message.from_user.id, name)
    if plan:
        md = format_daily_markdown(plan["daily"])
        await message.answer(f"План: *{plan['name']}*\nКкал: {plan['kcal']}  Б: {plan['protein']}  Ж: {plan['fat']}  У: {plan['carbs']}", parse_mode="Markdown", reply_markup=plans_after_kb())
        await message.answer(md)
        return
    await message.answer("Не распознал команду. Используйте главное меню или /start.", reply_markup=main_menu_kb())

# -------------------- Запуск --------------------
if __name__ == "__main__":
    print("Инициализация DB и запуск бота...")
    asyncio.run(init_db())
    asyncio.run(dp.start_polling(bot))
