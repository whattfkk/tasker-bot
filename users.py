import sqlite3

# Устанавливаем соединение с базой данных
connection = sqlite3.connect('bot_users.db')
cursor = connection.cursor()

# Создаем таблицу Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
tgid TEXT NOT NULL,
username TEXT NOT NULL,
password TEXT NOT NULL)
''')

# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()