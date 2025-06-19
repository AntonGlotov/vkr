import requests
import json
import sqlite3


def tf_idf_matrix(name, key, count_line):

    con = sqlite3.connect('C:/Универ/3 курс/Курсовая 2/Parcer1/my_database.sqlite3')
    cursor = con.cursor()

    cursor.execute('SELECT short_link, name, keywords, code_count FROM Articles LIMIT 1000')
    data = cursor.fetchall()

    flag = True
    while flag:
        mess = f'Я отправлю тебе фрагмент базы данных, в нем находится список статей, тебе нужно найти 10 наиболее похожих статьей на эту {name}, Ключевые слова: {key}, Количество строк кода: {count_line} . Ориентируйся на название статьи, ключевые слова и количество строк кода. Отдельное внимание уделяй названиям языков программирования и фреймворков, например python, go, fastapi и так далее.В ответ напиши только 10 шестизначных id статей через запятую. Важно, в ответ отправляй только те id, которые присутствуют в исходном файле. Вот сам файл: {data}'
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
            },
            data=json.dumps({
                "model": "google/gemini-2.5-flash",  # Optional
                "messages": [
                    {
                        "role": "user",
                        "content": mess
                    }
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ids",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "first": {
                                    "type": "number",
                                    "description": "Первая статья из наиболее похожих. id шестизначное"
                                },
                                "second": {
                                    "type": "number",
                                    "description": "Вторая статья из наиболее похожих. id шестизначное"
                                },
                                "third": {
                                    "type": "number",
                                    "description": "Третья статья из наиболее похожих. id шестизначное"
                                },
                                "fourth": {
                                    "type": "number",
                                    "description": "Четвёртая статья из наиболее похожих. id шестизначное"
                                },
                                "fifth": {
                                    "type": "number",
                                    "description": "Четвёртая статья из наиболее похожих. id шестизначное"
                                },
                                "sixth": {
                                    "type": "number",
                                    "description": "Четвёртая статья из наиболее похожих. id шестизначное"
                                },
                            },
                            "required": ["first", "second", "third", "fourth", "fifth", "sixth"],
                            "additionalProperties": False
                        }
                    }
                }
            })
        )
        print(response.json())
        if len(response.json()) > 3:

            with open('C:/Универ/4 курс/Диплом/example.txt', 'a', encoding='utf-8') as file:

                file.write(f'{str(response.json())}\n')
                return response.json()['choices'][0]['message']['content']

