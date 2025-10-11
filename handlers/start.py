# handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import main_menu_kb, back_kb_single

router = Router()

# создаём мини-StatesGroup для примера (в других модулях будем свои состояния)
class SimpleSG(StatesGroup):
    dummy = State()

# --- универсальный handler для кнопки "⬅️ Назад" ---
# регистрация этого хэндлера находится раньше, чтобы он перехватывал "Назад" до других обработчиков
@router.message(F.text == "⬅️ Назад")
async def handle_back(message: Message, state: FSMContext):
    """
    Универсальный обработчик '⬅️ Назад'.
    Логика: если есть активное состояние — переходим назад/чистим контекст,
    если состояния нет — просто возвращаем в главное меню.
    """
    current = await state.get_state()
    if current:
        # простая политика: очищаем стейт и возвращаем в меню
        await state.clear()
        await message.answer("Возврат. Вы в меню.", reply_markup=main_menu_kb())
    else:
        await message.answer("Вы уже в меню.", reply_markup=main_menu_kb())

# --- /start ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # не инициализируем БД здесь (делаем это в main.py один раз)
    await state.clear()
    await message.answer(
        "Привет! 👋\nЯ помогу составить план питания и список покупок.\n\nВыбери действие в меню ниже.",
        reply_markup=main_menu_kb()
    )

# --- помощь ---
@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Используй кнопки меню:\n"
        "• 🆕 Создать план — запустить анкету\n"
        "• 📋 Мои планы — посмотреть сохранённые\n"
        "• 🧾 Список покупок — сформировать покупки\n\nВ любой момент нажми «⬅️ Назад» для отмены/выхода.",
        reply_markup=main_menu_kb()
    )

# --- переход в создание плана (маршрутизатор только регистрирует команду, подробную анкету в отдельном модуле) ---
@router.message(F.text == "🆕 Создать план")
async def start_create_plan(message: Message, state: FSMContext):
    # Перенаправляем пользователя к модулю создания плана:
    # установим простое состояние, чтобы показать пример. Полную логику анкеты вынесем в handlers/plan_create.py
    await state.set_state(SimpleSG.dummy)
    await message.answer("Переходим к созданию плана — модуль анкеты загружен (в следующем шаге).", reply_markup=back_kb_single())

# --- заглушка: открыть меню "Мои планы" ---
@router.message(F.text == "📋 Мои планы")
async def my_plans_stub(message: Message):
    await message.answer("Модуль 'Мои планы' подключится в следующем шаге.", reply_markup=main_menu_kb())

# --- заглушка: список покупок ---
@router.message(F.text == "🧾 Список покупок")
async def shopping_stub(message: Message):
    await message.answer("Модуль 'Список покупок' подключится в следующем шаге.", reply_markup=main_menu_kb())
