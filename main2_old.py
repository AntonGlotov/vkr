import json
import nltk
import numpy as np
import requests
import re
import streamlit as st
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

st.set_page_config(
    page_title="Сайт",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://my-support.com'
    }
)

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

        # Извлечение текста и объединение его в одну строку
        if article_content:
            article_text = ' '.join(article_content.stripped_strings)
        else:
            article_text = ""

        return article_text, code_lines_count
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


# Загрузка данных
urls = fetch_urls('C:/Универ/3 курс/Курсовая 2/Parcer1/articles_11_05_2025.json')

# Получение текста статей и количества строк кода
article_texts_and_code_counts = {url: fetch_article_and_code_count(url) for url in urls}

# Разделение текстов статей и количества строк кода
article_texts = {url: text for url, (text, _) in article_texts_and_code_counts.items()}
code_counts = {url: code_count for url, (_, code_count) in article_texts_and_code_counts.items()}

# Запись текста статей и количества строк кода в JSON файл
# with open(f"articlesJ.json", "w", encoding='utf-8') as f:
#     try:
#         json.dump(article_texts_and_code_counts, f, indent=4, ensure_ascii=False)
#         print('Статьи были успешно получены')
#     except:
#         print('Статьи не удалось получить')

# Предварительная обработка текста
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('russian'))


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
    return ' '.join(tokens)


processed_articles = {url: preprocess_text(content) for url, content in article_texts.items()}

# Извлечение ключевых слов и тем с помощью TF-IDF
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(processed_articles.values())
tfidf_feature_names = vectorizer.get_feature_names_out()

# Добавление количества строк кода
code_counts_array = np.array([code_counts[url] for url in processed_articles.keys()]).reshape(-1, 1)
features_matrix = np.hstack((tfidf_matrix.toarray(), code_counts_array))


# Функция для получения ключевых слов
def get_keywords(tfidf_matrix, feature_names, top_n=10):
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


def cosine_sim_matrix():
    keywords = get_keywords(tfidf_matrix, tfidf_feature_names)

    user_url = st.text_input('')
    fetch_article_and_code_count(user_url)

    array = []
    list_of_articles = fetch_urls_and_articles('C:/Универ/3 курс/Курсовая 2/Parcer1/articles_11_05_2025.json')
    print(list_of_articles)
    for key, values in list_of_articles.items():
        dict = {}
        dict['ID'] = re.findall(r'\d+', values)
        dict['name'] = key
        dict['Ключевые слова'] = keywords[values]
        dict['Количество строк кода'] = code_counts[values]
        array.append(dict)

    with open("recommend_art.json", "w", encoding='utf-8') as f:
        try:
            json.dump(array, f, indent=4, ensure_ascii=False)
            print('Статьи были успешно получены')
        except:
            print('Статьи не удалось получить')

    print(len(array))


# Пример
# article_url = urls[0]
# recommendations = get_recommendations(article_url, features_matrix, list(processed_articles.keys()))
#
# # Вывод результатов
# print(f"Ключевые слова для {article_url}: {keywords[article_url]}")
# print(f"Рекомендации: {recommendations}")
# print(f"Количество строк кода в : {code_counts[article_url]}")

if __name__ == '__main__':
    # Вывод всего для всех статей
    keywords = get_keywords(tfidf_matrix, tfidf_feature_names)
    for url in urls:
        print(f"\nURL статьи: {url}")
        print(f"Ключевые слова: {keywords[url]}")
        print(f"Рекомендации: {get_recommendations(url, features_matrix, list(processed_articles.keys()))}")
        print(f"Количество строк кода: {code_counts[url]}")
