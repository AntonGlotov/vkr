import json
import nltk
import numpy as np
import requests
import re
import sys
import types
import base64
import time
import sqlite3
import streamlit as st
import webbrowser
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sklearn170
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from parcing import extract_keywords, find_name

# Предварительная обработка текста
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

stop_words = set(stopwords.words('russian'))

st.set_page_config(
    page_title="Сайт",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://my-support.com'
    }
)

# st.markdown(
#     """
#     <style>
#     body, .stTextInput, .stSelectbox, .stSlider, .stMarkdown, .stButton, .stDataFrame {
#         color: #000000 !important;
#     .stApp {
#         background-color: #FFFFFF;
#
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

st.write('# Введите ссылку на статью')


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


def fetch_urls_and_articles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data1 = json.load(f)

    return data1


# Функция для получения URL из файла
def fetch_urls(file_path):
    # Открытие файла и чтение данных
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)  # Загружаем JSON данные из файла

    # Извлечение всех URL из загруженных данных
    urls = list(data.values())

    return urls


def download_data():
    # Загрузка данных
    urls = fetch_urls('C:/Универ/3 курс/Курсовая 2/Parcer1/articles_12_05_2025.json')

    # Получение текста статей и количества строк кода
    article_texts_and_code_counts = {url: fetch_article_and_code_count(url) for url in urls}

    # Разделение текстов статей и количества строк кода
    article_texts = {url: text for url, (text, _) in article_texts_and_code_counts.items()}
    code_counts = {url: code_count for url, (_, code_count) in article_texts_and_code_counts.items()}

    return article_texts, code_counts


# Запись текста статей и количества строк кода в JSON файл
# with open(f"articlesJ.json", "w", encoding='utf-8') as f:
#     try:
#         json.dump(article_texts_and_code_counts, f, indent=4, ensure_ascii=False)
#         print('Статьи были успешно получены')
#     except:
#         print('Статьи не удалось получить')


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]

    return ' '.join(tokens)


def tfidf_keywords():
    article_texts, code_counts = download_data()
    processed_articles = {url: preprocess_text(content) for url, content in article_texts.items()}

    # Извлечение ключевых слов и тем с помощью TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(processed_articles.values())
    tfidf_feature_names = vectorizer.get_feature_names_out()

    # Добавление количества строк кода
    code_counts_array = np.array([code_counts[url] for url in processed_articles.keys()]).reshape(-1, 1)
    features_matrix = np.hstack((tfidf_matrix.toarray(), code_counts_array))

    return processed_articles, features_matrix, code_counts_array


# Функция для получения ключевых слов
def get_keywords(tfidf_matrix, feature_names, top_n=10):
    processed_articles, features_matrix, code_counts_array = tfidf_matrix
    keywords = {}

    for idx in range(tfidf_matrix.shape[0]):
        article = tfidf_matrix[idx].toarray().flatten()
        scores = article
        sorted_indices = scores.argsort()[::-1]
        top_feature_indices = sorted_indices[:top_n]
        keywords[list(processed_articles.keys())[idx]] = [feature_names[i] for i in top_feature_indices]

    return keywords


# Построение рекомендательного алгоритма
def get_recommendations(article_url, features_matrix, article_list, top_n=3):
    article_idx = article_list.index(article_url)
    cosine_similarities = cosine_similarity(features_matrix[article_idx:article_idx + 1], features_matrix).flatten()

    print(cosine_similarities)
    similar_indices = cosine_similarities.argsort()[::-1][1:top_n + 1]
    recommendations = [article_list[i] for i in similar_indices]

    return recommendations


# st.markdown("""
# <style>
#     .stTextInput>div>div>input {
#         color: black;
#         background-color: white;
#     }
# </style>
# """, unsafe_allow_html=True)

def is_habr_url(url):
    pattern = r'^https://habr\.com/ru/([a-zA-Z0-9\-_/]+/)?[0-9]{6}/?$'
    return bool(re.fullmatch(pattern, url))


correct_url = False

user_input_url = st.text_input('')
if not is_habr_url(user_input_url) and user_input_url:
    correct_url = False
    st.write('Некорректный URL адресс')

else:
    correct_url = True
# def func(user_input_url):
if user_input_url and correct_url:
    con = sqlite3.connect('C:/Универ/3 курс/Курсовая 2/Parcer1/my_database.sqlite3')
    cursor = con.cursor()
    cursor.execute('SELECT name, keywords, code_count FROM Articles WHERE link=?', (user_input_url,))

    results = cursor.fetchall()
    if results:
        name, key, code = results[0][0], results[0][1], results[0][2]
        sklearn170.tf_idf_matrix(name, key, code)

    else:
        text, code = fetch_article_and_code_count(user_input_url)
        key = extract_keywords(text)
        name = find_name(user_input_url)

    words = key.split()

    result = ', '.join(words[:-1]) + ' ' + words[-1]
    st.write(f'Название: {name}')
    st.write(f'Ключевые слова : {result}')
    st.write(f'Количество строк кода : {code}')

    st.markdown("<h1 style='text-align: center;'>Рекомендации</h1>", unsafe_allow_html=True)

    recomend = sklearn170.tf_idf_matrix(name, key, code)
    # st.write(recomend)
    recommendations = json.loads(recomend)

    recs = []
    numbers = ["first", "second", "third", "fourth", "fifth", "sixth"]
    for position in numbers:
        cursor.execute('SELECT name, link, keywords, code_count FROM Articles WHERE short_link=?',
                       (recommendations[position],))
        rec = cursor.fetchall()
        recs.append(rec)

    recomendation = [x for x in recs if x]

    i = 1

    while i < len(recomendation) and i <= 4:

        if recomendation[i][0][1] == user_input_url:
            del recomendation[i][0]
            i += 1

        words = recomendation[i][0][2].split()
        result1 = ', '.join(words[:-1]) + ' ' + words[-1]

        st.markdown(
            f'<a href="{recomendation[i][0][1]}" style="color: #FFFFFF; font-weight: bold;">{i-1} {recomendation[i][0][0]}</a>',
            unsafe_allow_html=True
        )
        st.write(
            f"""
            <div style='color: #FFFFFF;'>
                Ключевые слова: {result1}<br>
                Количество строк кода: {recomendation[i][0][3]}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write('')
        i += 1


def dump_json_matrix(user_url):
    con = sqlite3.connect('C:/Универ/3 курс/Курсовая 2/Parcer1/my_database.sqlite3')
    cursor = con.cursor()
    con.execute('SELECT keywords FROM Articles')
    x = cursor.fetchall()
    con.close()
    keyword = extract_keywords(x)

    print(fetch_article_and_code_count(user_url))
    get_recommendations(user_url, x, keyword)
    array = []
    list_of_articles = fetch_urls_and_articles('C:/Универ/3 курс/Курсовая 2/Parcer1/articles_12_05_2025.json')
    print(list_of_articles)
    for key, values in list_of_articles.items():
        dict = {}
        dict['ID'] = values[17::]
        dict['name'] = key
        dict['Ключевые слова'] = keyword[values]
        # dict['Количество строк кода'] = code_counts[values]
        array.append(dict)
    get_recommendations(user_url, array, keyword)
    with open("recommend_art.json", "w", encoding='utf-8') as f:
        try:
            json.dump(array, f, indent=4, ensure_ascii=False)
            print('success')
        except:
            print('error')

    print(len(array))


# if __name__ == '__main__':
#     start = time.time()
#     get_recommendations('https://habr.com/ru/companies/amvera/articles/907990/')
#     end = time.time()
#     print(end-start)

# Пример
# article_url = urls[0]
# recommendations = get_recommendations(article_url, features_matrix, list(processed_articles.keys()))
#
# # Вывод результатов
# print(f"Ключевые слова для {article_url}: {keywords[article_url]}")
# print(f"Рекомендации: {recommendations}")
# print(f"Количество строк кода в : {code_counts[article_url]}")

# if __name__ == '__main__':
#     # Вывод всего для всех статей
#     keywords = get_keywords(tfidf_matrix, tfidf_feature_names)
#     for url in urls:
#         print(f"\nURL статьи: {url}")
#         print(f"Ключевые слова: {keywords[url]}")
#         # print(f"Рекомендации: {get_recommendations(url, features_matrix, list(processed_articles.keys()))}")
#         print(f"Количество строк кода: {code_counts[url]}")
