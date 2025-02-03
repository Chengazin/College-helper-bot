import asyncio 
from aiogram import Bot, Dispatcher, Router, F 
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.filters import Command 
from aiogram.utils.markdown import hlink, bold 
import json

TOKEN = '7768199477:AAHTFJvKwCkoM76ZJ4NGz0s10d9046G5EEU'  # Замените на свой токен бота 

# --- База данных статей (замените на свои) --- 
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    articles_db = json.load(f)

# Преобразуем список статей в словарь для более удобного поиска
articles_dict = {article["title"]: article for article in articles_db}

# --- Обработчики сообщений --- 
router = Router() 

@router.message(Command(commands=["start", "help"])) 
async def start_handler(message: Message): 
    await message.answer( 
        "Привет! Я бот, который поможет тебе найти статьи на сайте техникума.\n" 
        "Просто напиши мне тему, которая тебя интересует." 
    ) 

@router.message(F.text) 
async def text_handler(message: Message): 
    user_text = message.text.lower() 
    found_articles = [] 

    for article in articles_db: 
        if any(keyword.lower() in user_text for keyword in article["keywords"]):
            found_articles.append(article)
    
    if found_articles: 
        await message.answer("Вот что я нашёл по вашему запросу:") 
        for article in found_articles: 
           await message.answer( 
               hlink(article["title"], article["url"]), 
               parse_mode="HTML" 
           ) 
    else: 
        await message.answer( 
            "К сожалению, по вашему запросу ничего не найдено. " 
            "Попробуйте использовать другие ключевые слова." 
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