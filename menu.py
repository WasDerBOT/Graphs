import sqlite3

# Устанавливаем соединение с базой данных
connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

# Создаем таблицу Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
username TEXT NOT NULL,
time INTEGER
)
''')
cursor.execute('INSERT INTO Users (username, time) VALUES (?, ?)', ('test1', 186))
# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()