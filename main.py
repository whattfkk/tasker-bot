import telebot
import config
import requests
import sqlite3
from requests.auth import HTTPBasicAuth

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'привет! для авторизации отправь команду /login')

@bot.message_handler(commands=['login'])
def login(message):
    data = bot.send_message(message.chat.id, 'в следующем сообщении отправь свой логин и пароль в таком формате:\n\nлогин\nпароль\n\nесли у тебя их нет, отправь команду /register.')
    bot.register_next_step_handler(data, login1)
def login1(message):
    splitted = message.text.split('\n')
    login = splitted[0]
    password = splitted[1]
    login_request = requests.post(f'{config.api}/login', json = {"login": login, "password": password})
    if login_request.json()['success'] == 'true':
        connection = sqlite3.connect('bot_users.db')
        cursor = connection.cursor()
        cursor.execute('SELECT tgid FROM Users WHERE tgid = ?', (message.from_user.id,))
        results = cursor.fetchall()
        if results:
            pass
        else:
            cursor.execute('INSERT INTO Users (tgid, username, password) VALUES (?, ?, ?)', (message.from_user.id, login, password))
            connection.commit()
            connection.close()
        bot.send_message(message.chat.id, f'привет, {login}! теперь ты можешь выполнять другие команды, они доступны в меню снизу.')
    else:
        bot.send_message(message.chat.id, 'логин или пароль неверен. попробуй авторизоваться заново через /login.')

@bot.message_handler(commands=['register'])
def register(message):
    data = bot.send_message(message.chat.id, 'введи свое новое имя пользователя и пароль в таком формате:\n\nлогин\nпароль')
    bot.register_next_step_handler(data, register1)
def register1(message):
    splitted = message.text.split('\n')
    login = splitted[0]
    password = splitted[1]
    register_request = requests.post(f'{config.api}/create_account', json = {"login": login, "password": password})
    if register_request.text == 'This username already registered.':
        bot.send_message(message.chat.id, 'выбери другое имя пользователя, это уже занято.')
    elif register_request.json()['success'] == 'true':
        connection = sqlite3.connect('bot_users.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO Users (tgid, username, password) VALUES (?, ?, ?)', (message.from_user.id, login, password))
        connection.commit()
        connection.close()
        bot.send_message(message.chat.id, f'привет, {login}! теперь ты можешь выполнять другие команды, они доступны в меню снизу.')

@bot.message_handler(commands=['view_tasks'])
def view_tasks(message):
    connection = sqlite3.connect('bot_users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT tgid, username, password FROM Users WHERE tgid = ?', (message.from_user.id,))
    results = cursor.fetchall()
    login = results[0][1]
    password = results[0][2]
    all_tasks = requests.get(f'{config.api}/get_tasks', auth = HTTPBasicAuth(str(login), password))
    print(all_tasks.json())
    string = ''
    for i in all_tasks.json():
        if i['is_done'] == 'false':
            temp = f'{i['text']}, статус: не выполнена, id: {i['id']}.'
            string = string + temp + '\n'
        elif i['is_done'] == 'true':
            temp = f'{i['text']}, статус: выполнена, id: {i['id']}.'
            string = string + temp + '\n'
    bot.send_message(message.chat.id, f'твои задачи:\n\n{string}')
    connection.close()

@bot.message_handler(commands=['create_task'])
def create_task(message):
    data = bot.send_message(message.chat.id, 'что должно быть в задаче?')
    bot.register_next_step_handler(data, create_task1)
def create_task1(message):
    connection = sqlite3.connect('bot_users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT tgid, username, password FROM Users WHERE tgid = ?', (message.from_user.id,))
    results = cursor.fetchall()
    login = results[0][1]
    password = results[0][2]
    create_task_request = requests.post(f'{config.api}/create_task', auth = HTTPBasicAuth(str(login), password), json = {"text": message.text})
    print(create_task_request.json())
    if create_task_request.json()['success'] == 'true':
        bot.send_message(message.chat.id, f'задача "{message.text}" создана, ее id: {create_task_request.json()['id']}')
    connection.close()

@bot.message_handler(commands=['edit_task'])
def edit_task(message):
    data = bot.send_message(message.chat.id, 'отправь id задачи и ее новый текст в таком формате:\n\nid\nтекст')
    bot.register_next_step_handler(data, edit_task1)
def edit_task1(message):
    connection = sqlite3.connect('bot_users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT tgid, username, password FROM Users WHERE tgid = ?', (message.from_user.id,))
    results = cursor.fetchall()
    login = results[0][1]
    password = results[0][2]
    splitted = message.text.split('\n')
    idd = splitted[0]
    new_text = splitted[1]
    edit_task_request = requests.put(f'{config.api}/edit_task/{idd}', auth = HTTPBasicAuth(str(login), password), json = {"text": new_text})
    if edit_task_request.json()['success'] == 'true':
        connection.close()
        bot.send_message(message.chat.id, f'задача {idd} изменена, новый текст:\n\n{new_text}')
    elif edit_task_request.json()['success'] == 'false':
        if edit_task_request.json()['cause'] == 'this task was made by other person.':
            connection.close()
            bot.send_message(message.chat.id, 'эта задача была сделана другим человеком.')
        elif edit_task_request.json()['cause'] == 'task not exist':
            connection.close()
            bot.send_message(message.chat.id, 'задачи с таким id не существует.')

@bot.message_handler(commands=['delete_task'])
def delete_task(message):
    data = bot.send_message(message.chat.id, 'введи id задачи, которую нужно удалить.')
    bot.register_next_step_handler(data, delete_task1)
def delete_task1(message):
    connection = sqlite3.connect('bot_users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT tgid, username, password FROM Users WHERE tgid = ?', (message.from_user.id,))
    results = cursor.fetchall()
    login = results[0][1]
    password = results[0][2]
    delete_task_request = requests.delete(f'{config.api}/delete_task/{message.text}', auth = HTTPBasicAuth(str(login), password))
    if delete_task_request.json()['success'] == 'true':
        connection.close()
        bot.send_message(message.chat.id, f'задача {message.text} удалена.')
    elif delete_task_request.json()['success'] == 'false':
        if delete_task_request.json()['cause'] == 'this task was made by other person.':
            connection.close()
            bot.send_message(message.chat.id, 'эта задача была сделана другим человеком.')
        elif delete_task_request.json()['cause'] == 'task not exist':
            connection.close()
            bot.send_message(message.chat.id, 'этой задачи не существует.')

@bot.message_handler(commands=['task_done'])
def task_done(message):
    data = bot.send_message(message.chat.id, 'напиши id задачи, которой ты хочешь изменить статус.')
    bot.register_next_step_handler(data, task_done1)
def task_done1(message):
    connection = sqlite3.connect('bot_users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT tgid, username, password FROM Users WHERE tgid = ?', (message.from_user.id,))
    results = cursor.fetchall()
    login = results[0][1]
    password = results[0][2]
    task_done_request = requests.put(f'{config.api}/task_done/{message.text}', auth = HTTPBasicAuth(str(login), password))
    if task_done_request.json()['success'] == 'true':
        if task_done_request.json()['is_done'] == 'true':
            connection.close()
            bot.send_message(message.chat.id, f'задача {message.text} выполнена.')
        elif task_done_request.json()['is_done'] == 'false':
            connection.close()
            bot.send_message(message.chat.id, f'задача {message.text} не выполнена.')
    elif task_done_request.json()['success'] == 'false':
        if task_done_request.json()['cause'] == 'this task was made by other person.':
            connection.close()
            bot.send_message(message.chat.id, 'эта задача была сделана другим человеком.')
        elif task_done_request.json()['cause'] == 'task not exist':
            connection.close()
            bot.send_message(message.chat.id, 'задачи с таким id не существует.')

bot.polling(interval = 0, none_stop = True)