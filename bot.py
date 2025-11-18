import os
import logging
from pathlib import Path

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import FSInputFile

# ================== ЛОГИ ==================
logging.basicConfig(level=logging.INFO)

# ================== БОТ ==================
bot = Bot(token=os.getenv("BOT_TOKEN"))
bot = bot.with_parse_mode("HTML")
dp = Dispatcher()

# ================== ЗАГРУЗКА ПРАЙСА ==================
df = pd.DataFrame()

def load_price():
    global df
    try:
        df = pd.read_excel("price.xlsx", dtype=str)
        # Цена и остаток → числа
        df['Цена'] = pd.to_numeric(df['Цена'], errors='coerce').fillna(0).astype(int)
        df['Остаток'] = pd.to_numeric(df['Остаток'], errors='coerce').fillna(0).astype(int)
        logging.info(f"Прайс загружен: {len(df)} позиций")
    except Exception as e:
        logging.error(f"Ошибка загрузки прайса: {e}")

load_price()

# ================== КОМАНДЫ ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Напиши любое слово — найду товары из прайса.\n\n"
        "Пример: яблоко, груша, банан\n"
        "Новый прайс можно просто перезалить в репозиторий — обновлюсь автоматически!"
    )

# ================== ПОИСК ==================
@dp.message(F.text)
async def search(message: types.Message):
    query = message.text.strip().lower()
    if len(query) < 2:
        await message.answer("Минимум 2 буквы")
        return

    if df.empty:
        await message.answer("Прайс пока пустой...")
        return

    mask = df['Наименование'].str.lower().str.contains(query, na=False)
    results = df[mask]

    if results.empty:
        await message.answer(f"По запросу «{message.text}» ничего не нашёл")
        return

    lines = []
    for _, row in results.iterrows():
        name = row['Наименование']
        price = row['Цена']
        stock = row['Остаток']
        emoji = "В наличии" if stock > 0 else "Нет"
        line = f"{emoji} <b>{name}</b> — {price}₽"
        if stock > 0:
            line += f" (ост. {stock} шт.)"
        lines.append(line)

    text = f"Найдено <b>{len(results)}</b>:\n\n" + "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(lines), 30):
            chunk = "\n".join(lines[i:i+30])
            await message.answer(chunk)
    else:
        await message.answer(text)

# ================== ЗАПУСК ==================
async def main():
    logging.info("Бот запущен на Render")
    await dp.start_polling(bot)

if name == "__main__":
    import asyncio
    asyncio.run(main())
