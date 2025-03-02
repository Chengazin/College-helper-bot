import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import json
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
from fuzzywuzzy import fuzz  # Требуется установить fuzzywuzzy (и желательно python-Levenshtein)
from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

TOKEN = os.getenv('TOKEN') # Замените на свой токен бота

# --- Загрузка базы знаний ---
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    articles_db = json.load(f)

# --- Загрузка модели T5 ---
model_name = "t5-small"  # Можно использовать "t5-base" или "t5-large"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# --- Функция ранжирования статей с помощью T5 ---
def rank_articles(user_text, articles_db, top_n=3):
    input_texts = [f"rank: {user_text} {article['title']}" for article in articles_db]
    input_ids = tokenizer.batch_encode_plus(input_texts, return_tensors="pt", padding=True, truncation=True)
    try:
        with torch.no_grad():
            outputs = model(**input_ids)
        scores = outputs.logits.mean(dim=1).tolist()
        ranked_articles = sorted(zip(scores, articles_db), reverse=True)
        return [article for _, article in ranked_articles[:top_n]]
    except Exception as e:
        print(f"Error during ranking: {str(e)}")
        return []

# --- Функция поиска по ключевым словам с нечетким сравнением ---
def search_by_keywords(query, articles_db, threshold=90):
    results = []
    tokens = [token for token in query.lower().split() if len(token) >= 3]  # фильтруем короткие слова
    for article in articles_db:
        article_keywords = [kw.lower() for kw in article.get("keywords", [])]
        for token in tokens:
            for kw in article_keywords:
                ratio = fuzz.ratio(token, kw)
                if ratio >= threshold or token in kw or kw in token:
                    results.append(article)
                    break
            else:
                continue
            break
    return results

# --- Обработчики сообщений ---
router = Router()

@router.message(Command(commands=["start", "help"]))
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я бот, который поможет тебе найти информацию на сайте техникума.\n"
        "Просто напиши мне свой вопрос."
    )

@router.message(F.text)
async def text_handler(message: Message):
    user_text = message.text.lower()

    # Сначала пробуем поиск по ключевым словам
    keyword_results = search_by_keywords(user_text, articles_db)
    if keyword_results:
        # Ограничиваем вывод до 3 статей и формируем inline‑кнопки (каждая кнопка в отдельной строке)
        limited_results = keyword_results[:3]
        buttons = [InlineKeyboardButton(text=article["title"], url=article["url"]) for article in limited_results]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
        await message.answer("Вот статьи, найденные по ключевым словам:", reply_markup=keyboard)
        return

    # Если по ключевым словам ничего не найдено – ранжирование с помощью T5
    ranked_articles = rank_articles(user_text, articles_db, top_n=3)
    if ranked_articles:
        buttons = [InlineKeyboardButton(text=article["title"], url=article["url"]) for article in ranked_articles]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
        await message.answer("Вот наиболее подходящие статьи по вашему запросу:", reply_markup=keyboard)
        return

    # Фолбэк: генерация ответа с помощью T5
    input_text = f"ответ на вопрос: {user_text}"
    input_ids = tokenizer.encode(input_text, return_tensors="pt")
    try:
        output_ids = model.generate(input_ids, max_length=200, num_beams=4, early_stopping=True)
        response = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        print(f"Generated response: {response}")
    except Exception as e:
        response = f"Произошла ошибка при обработке запроса: {str(e)}"
        print(f"Error during response generation: {str(e)}")
    
    await message.answer(
        f"По вашему запросу ничего не найдено, но вот возможный ответ:\n{response}\n\n"
        "Я могу помочь найти статьи на сайте техникума. Просто задайте конкретный вопрос!"
    )

# --- Запуск бота ---
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Finish')
