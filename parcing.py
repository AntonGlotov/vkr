from bs4 import BeautifulSoup
import time
import sys
import re
import sqlite3
import requests
from fake_useragent import UserAgent
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import string
from nltk import ngrams
import pymorphy3


def find_name(url):
    ua = UserAgent()

    headers = {
        'accept': 'application/json, text/plain, */*',
        'user-Agent': ua.google,
    }
    req = requests.get(url, headers=headers).text

    soup = BeautifulSoup(req, 'lxml')
    all_hrefs_articles = soup.find('title').text  # получаем статьи

    return all_hrefs_articles


def progress_bar(current, total, bar_length=100):
    fraction = current / total
    filled_length = int(bar_length * fraction)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percentage = fraction * 100
    sys.stdout.write(f'\rШаг {current}/{total} |{bar}| {percentage:.1f}% ')
    sys.stdout.flush()


def parcing(urls, clear=True):
    if clear:
        connection = sqlite3.connect('C:/Универ/3 курс/Курсовая 2/Parcer1/my_database.sqlite3')
        cursor = connection.cursor()

        cursor.execute('DELETE FROM Articles')

        connection.commit()
        connection.close()

    i = 0
    total_iterations = len(urls) * 20

    for url in urls:
        ua = UserAgent()

        headers = {
            'accept': 'application/json, text/plain, */*',
            'user-Agent': ua.google,
        }

        req = requests.get(url, headers=headers).text

        soup = BeautifulSoup(req, 'lxml')
        all_hrefs_articles = soup.find_all('a', class_='tm-title__link')  # получаем статьи

        for article in all_hrefs_articles:  # проходимся по статьям

            article_name = article.find('span').text  # собираем названия статей
            article_link = f'https://habr.com{article.get("href")}'

            progress_bar(i + 1, total_iterations)
            i += 1

            text, code_count, site_keywords = fetch_article_and_code_count(article_link)
            if text == '' and code_count == 0 and site_keywords == '':
                continue

            keyword = extract_keywords(text, top_n=(10 - len(site_keywords.split())))
            keyword += (site_keywords)
            regular = re.findall(r"\b\d+\b", article_link)
            short_link = regular[0] if regular else None
            con = sqlite3.connect('C:/Универ/3 курс/Курсовая 2/Parcer1/my_database.sqlite3')
            cursor = con.cursor()
            cursor.execute('SELECT link FROM Articles WHERE link = ?', (article_link,))
            res = cursor.fetchall()
            if res:
                cursor.execute('INSERT INTO Articles (link, short_link, name, keywords, code_count) VALUES (?, ?, ?, ?, ?)',
                           (article_link, short_link, article_name, keyword, code_count))


            con.commit()
            # con.close()

            # article_dict['Название'] = article_name
            # article_dict['Ссылка'] = article_link
            # article_dict['Ключевые слова'] = keyword
            # article_dict['Количество строк кода'] = code_count
            # articles_json.append(article_dict)

    # return articles_json


# Функция для получения текста статьи и подсчета строк кода
def fetch_article_and_code_count(url):
    try:
        ua = UserAgent()

        headers = {
            'accept': 'application/json, text/plain, */*',

            'user-Agent': ua.google,
        }

        response = requests.get(url, headers=headers)

        response.raise_for_status()

        # Получаем код страницы
        soup = BeautifulSoup(response.text, 'lxml')

        # Поиск и подсчет строк кода
        code_blocks = soup.find_all(['code', 'pre'])
        code_lines_count = sum(block.get_text().count('\n') + 1 for block in code_blocks)

        # Удаление блоков кода для получения чистого текста статьи
        for code_block in code_blocks:
            code_block.decompose()

        # Поиск контента статьи
        article_content = soup.find('div',
                                    class_='article-formatted-body article-formatted-body article-formatted-body_version-1')

        if not article_content:
            article_content = soup.find('div',
                                        class_='article-formatted-body article-formatted-body article-formatted-body_version-2')

        hub_links = soup.find_all('a', class_='tm-publication-hub__link')

        hubs = ''
        pattern = r'^блог\b'
        for link in hub_links:
            hub_name = link.find('span').get_text(strip=True)
            if not re.match(pattern, hub_name, re.IGNORECASE):
                hubs += hub_name
                hubs += ' '



        # Извлечение текста и объединение его в одну строку
        if article_content:
            article_text = ' '.join(article_content.stripped_strings)
        else:
            article_text = ""
        if hubs and article_text and code_blocks:
            return str(article_text), code_lines_count, hubs
        else:
            return '', 0, ''

    except Exception as e:
        print(f"An error occurred: {e}")
        return "", 0


def extract_keywords1(text, num_keywords=10):

    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

    # Приведение к нижнему регистру и удаление пунктуации
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation + '«»–'))

    # Токенизация
    words = word_tokenize(text, language='russian')

    # Русские стоп-слова
    try:
        stop_words = set(stopwords.words('russian'))
    except LookupError:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('russian'))

    # Фильтрация (исключаем стоп-слова, числа и короткие слова)
    filtered_words = [
        word for word in words
        if (word not in stop_words)
           and (len(word) > 2)
           and (not word.isdigit())
    ]

    # Подсчет частоты
    word_counts = Counter(filtered_words)
    keywords = ''
    for word, _ in word_counts.most_common(num_keywords):
        keywords += word + ' '
    return keywords


nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)


def extract_keywords(text, top_n=10):
    # Инициализация инструментов
    morph = pymorphy3.MorphAnalyzer()
    russian_stopwords = set(stopwords.words('russian'))

    # Добавление кастомных стоп-слов
    custom_stopwords = ['который', 'задача', 'мочь', 'год', 'выбрать', 'это', 'затем', 'весь',
                        'ваш', 'дать', 'слово', 'наш', 'тип', 'дать', 'свой', 'имя', 'тест', 'куча',
                        'нажать', 'свой', 'разный', 'набор', 'сделать', 'близкий', 'наш', 'должный', 'сделка',
                        'нюанс', 'свой', 'часто', 'рисунок', 'зритель', 'сделать', 'кот', 'роль', 'дать', 'нужно',
                        'вдох', 'сон', 'время', 'бодрствование', 'самый', 'выживание', 'весь', 'очень', 'друг',
                        'нужно', 'ваш', 'никакой', 'стать', 'весь', 'строка', 'хук', 'очень', 'the',
                        'самый', 'наш', 'и', 'дать', 'образ', 'день', 'время', 'затем', 'хотеть', 'вывод',
                        'заходить', 'дать', 'открытый', 'каждый', 'большой', 'несколько', 'быстрый', 'простой',
                        'физический', 'нужно']

    if custom_stopwords:
        russian_stopwords.update(custom_stopwords)

    # Очистка текста и токенизация
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()

    # Извлечение биграмм для составных терминов
    bigrams = [' '.join(gram) for gram in ngrams(words, 2)]

    # Обработка слов и биграмм
    keywords = []
    for item in words + bigrams:
        # Морфологический анализ и нормализация
        parsed = morph.parse(item.split()[0])[0]  # для биграмм берем первое слово
        normal_form = parsed.normal_form

        # Проверка на стоп-слова и длину
        if (len(normal_form) > 2 and
                normal_form not in russian_stopwords and
                not parsed.tag.POS in {'PREP', 'CONJ', 'PRCL'}):

            # Для биграмм сохраняем оригинальную форму
            if ' ' in item:
                keywords.append(item)
            else:
                keywords.append(normal_form)

    # Подсчет частотности и фильтрация технических терминов
    counter = Counter(keywords)
    answ = counter.most_common(top_n)
    result = ''
    for x in answ:
        result += x[0]
        result += ' '

    return result


def generate_urls(base_url, start_page, end_page):
    urls = [f"{base_url}/page{i}/" for i in range(start_page, end_page + 1)]
    return urls


if __name__ == '__main__':
    base_url = 'https://habr.com/ru/flows/popsci/articles/'
    start_page = 1
    end_page = 50  # Количество страниц habr
    urls = generate_urls(base_url, start_page, end_page)
    # for url in urls:
    #     print(url)

    start = time.time()
    parcing(urls, clear=False)
    end = time.time()
    print(end - start)
