import requests
from bs4 import BeautifulSoup
import json

# Функция для получения контента страницы
def get_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Не удалось получить доступ к странице: {url}")
        return None

# Функция для парсинга контента страницы и сбора данных
def parse_page(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем все ссылки ниже элемента с id "jsn-header"
    links = []
    header = soup.find(id="jsn-header")
    if header:
        for link in header.find_all_next('a', href=True):
            if link['href'].startswith('http'):
                links.append(link['href'])
            else:
                links.append(base_url + link['href'])

    knowledge_base = []

    # Парсим каждую найденную ссылку
    for link in set(links):
        page_content = get_page_content(link)
        if page_content:
            sub_soup = BeautifulSoup(page_content, 'html.parser')

            # Получаем заголовок (title) страницы
            title_tag = sub_soup.find('title')
            title = title_tag.string if title_tag else 'No Title'

            # Получаем ключевые слова (keywords) из метатегов или текста страницы
            keywords = []
            meta_keywords = sub_soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                keywords = meta_keywords.get('content').split(', ')
            else:
                # Если нет метатегов, используем первые несколько слов текста как ключевые слова
                text = sub_soup.get_text()
                words = text.split()[:10]
                keywords = [word.strip() for word in words]

            # Добавляем элемент в базу знаний
            knowledge_base.append({
                "title": title,
                "url": link,
                "keywords": keywords
            })

    return knowledge_base

# Основная функция
def main():
    base_url = "http://promtis.com.ru/"
    start_url = "http://promtis.com.ru/index.php/abiturientu"

    html_content = get_page_content(start_url)
    if html_content:
        knowledge_base = parse_page(html_content, base_url)

        # Сохраняем базу знаний в файл JSON
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=4)

        print("База знаний успешно создана и сохранена в файл 'knowledge_base.json'.")

if __name__ == "__main__":
    main()