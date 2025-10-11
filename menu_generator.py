import random

# Продукты по категориям
PROTEINS = [
    {"name": "Куриная грудка", "protein": 23, "fat": 1.9, "carbs": 0, "kcal": 113},
    {"name": "Индейка", "protein": 21, "fat": 5, "carbs": 0, "kcal": 135},
    {"name": "Яйца", "protein": 12, "fat": 10, "carbs": 1, "kcal": 143},
    {"name": "Творог 5%", "protein": 17, "fat": 5, "carbs": 2, "kcal": 121},
    {"name": "Говядина постная", "protein": 20, "fat": 8, "carbs": 0, "kcal": 160},
    {"name": "Рыба (хек)", "protein": 17, "fat": 2, "carbs": 0, "kcal": 90},
]

CARBS = [
    {"name": "Рис", "protein": 7, "fat": 0.6, "carbs": 75, "kcal": 340},
    {"name": "Гречка", "protein": 13, "fat": 3.4, "carbs": 72, "kcal": 329},
    {"name": "Овсянка", "protein": 11, "fat": 6, "carbs": 62, "kcal": 352},
    {"name": "Картофель", "protein": 2, "fat": 0.4, "carbs": 16, "kcal": 80},
    {"name": "Макароны", "protein": 12, "fat": 1.5, "carbs": 72, "kcal": 340},
]

FATS = [
    {"name": "Оливковое масло", "protein": 0, "fat": 100, "carbs": 0, "kcal": 900},
    {"name": "Грецкие орехи", "protein": 16, "fat": 60, "carbs": 11, "kcal": 654},
    {"name": "Арахис", "protein": 25, "fat": 48, "carbs": 12, "kcal": 580},
    {"name": "Семечки", "protein": 20, "fat": 52, "carbs": 5, "kcal": 570},
]

VEGGIES = [
    {"name": "Брокколи", "protein": 3, "fat": 0.4, "carbs": 7, "kcal": 35},
    {"name": "Огурцы", "protein": 0.8, "fat": 0.1, "carbs": 3, "kcal": 15},
    {"name": "Помидоры", "protein": 0.9, "fat": 0.2, "carbs": 4, "kcal": 20},
    {"name": "Морковь", "protein": 1.3, "fat": 0.1, "carbs": 6.9, "kcal": 32},
]

def generate_meal_plan(total_protein, total_fat, total_carbs, total_kcal, meals=3):
    """
    Генерирует план питания на день с разнообразными продуктами
    """
    meal_plan = []
    p_per_meal = total_protein / meals
    f_per_meal = total_fat / meals
    c_per_meal = total_carbs / meals
    kcal_per_meal = total_kcal / meals

    for i in range(meals):
        protein_source = random.choice(PROTEINS)
        carb_source = random.choice(CARBS)
        fat_source = random.choice(FATS) if i != meals-1 else None  # жиры не обязательно на каждом приеме
        veg_source = random.choice(VEGGIES)

        # Примерно подбираем граммовку
        protein_g = round((p_per_meal / protein_source["protein"]) * 100, 0)
        carb_g = round((c_per_meal / carb_source["carbs"]) * 100, 0)
        veg_g = 100
        fat_g = round((f_per_meal / fat_source["fat"]) * 100, 0) if fat_source else 0

        items = [
            {"product": protein_source["name"], "g": protein_g, **protein_source},
            {"product": carb_source["name"], "g": carb_g, **carb_source},
            {"product": veg_source["name"], "g": veg_g, **veg_source},
        ]
        if fat_source:
            items.append({"product": fat_source["name"], "g": fat_g, **fat_source})

        # Подсчет приёма пищи
        meal_kcal = 0
        meal_p = 0
        meal_f = 0
        meal_c = 0
        for item in items:
            factor = item["g"] / 100
            meal_kcal += item["kcal"] * factor
            meal_p += item["protein"] * factor
            meal_f += item["fat"] * factor
            meal_c += item["carbs"] * factor

        meal_plan.append({
            "title": f"🍽 Приём пищи {i+1}",
            "items": items,
            "totals": {
                "kcal": round(meal_kcal),
                "protein": round(meal_p),
                "fat": round(meal_f),
                "carbs": round(meal_c)
            }
        })

    return meal_plan

def format_meal_plan(meal_plan, total_kcal, total_p, total_f, total_c):
    """
    Возвращает красиво отформатированное меню для Telegram (Markdown)
    """
    lines = []
    for meal in meal_plan:
        lines.append(f"{meal['title']} ({meal['totals']['kcal']} ккал)")
        for item in meal["items"]:
            lines.append(f"• {item['product']} — {int(item['g'])} г (Б {item['protein']} / Ж {item['fat']} / У {item['carbs']})")
        lines.append("")  # пустая строка

    lines.append(f"📊 *Итог за день:* {round(total_kcal)} ккал — Б {round(total_p)} / Ж {round(total_f)} / У {round(total_c)}")
    return "\n".join(lines)
