import sqlite3

if __name__ == '__main__':
    connection = sqlite3.connect('my_database.sqlite3')
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Articles (
    id INTEGER PRIMARY KEY,
    link TEXT NOT NULL,
    short_link TEXT NOT NULL,
    name TEXT NOT NULL,
    keywords TEXT NOT NULL,
    code_count INTEGER
    )
    ''')

    connection.commit()
    connection.close()
