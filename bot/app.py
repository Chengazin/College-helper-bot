
import inspect
if not hasattr(inspect, "getargspec"):
    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return spec.args, spec.varargs, spec.varkw, spec.defaults
    inspect.getargspec = getargspec
import asyncio
import os
import json
import re
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
import pymorphy2
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Отсутствует токен бота. Проверьте .env файл (переменная TOKEN).")
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    articles_db = json.load(f)

if not articles_db:
    raise ValueError("База знаний пуста. Проверьте файл knowledge_base.json.")
morph = pymorphy2.MorphAnalyzer()

def tokenize(text):
    words = re.findall(r'\w+', text.lower())
    return [morph.parse(word)[0].normal_form for word in words]

bm25_corpus = [
    tokenize(article["title"] + " " + " ".join(article.get("keywords", [])))
    for article in articles_db
]
bm25 = BM25Okapi(bm25_corpus)
def bm25_search(query, bm25, articles_db, top_n=3, threshold=0.1):
    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = [
        (scores[idx], articles_db[idx])
        for idx in sorted_indices[:top_n]
        if scores[idx] >= threshold
    ]
    return results
user_error_counts = {}
router = Router()
@router.message(Command(commands=["start", "help"]))
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_error_counts[user_id] = 0
    await message.answer("Привет! Я помогу найти информацию на сайте техникума. Просто напиши свой вопрос.")
@router.message(F.text)
async def text_handler(message: Message):
    user_text = message.text.strip()
    user_id = message.from_user.id
    bm25_results = bm25_search(user_text, bm25, articles_db, top_n=3, threshold=0.1)
    if bm25_results:
        user_error_counts[user_id] = 0
        buttons = [
            InlineKeyboardButton(text=article["title"], url=article["url"])
            for score, article in bm25_results
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
        await message.answer("Вот найденные статьи:", reply_markup=keyboard)
    else:
        current_errors = user_error_counts.get(user_id, 0) + 1
        user_error_counts[user_id] = current_errors
        if current_errors >= 3:
            await message.answer("Прощу прощения, кажется, я не могу помочь вам с вашим вопросом. Прилагаю номера телефонов поддержки техникума...")
            user_error_counts[user_id] = 0
        else:
            fallback_response = (
                f"К сожалению, по вашему запросу '{user_text}' информации не найдено.\n"
                "Попробуйте задать вопрос иначе."
            )
            await message.answer(fallback_response)
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен.')