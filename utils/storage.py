import json
import os

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

# Авторизованные пользователи
try:
    with open(os.path.join(DATA_DIR, 'authorized_users.json'), 'r', encoding='utf-8') as f:
        authorized_users = json.load(f)
except:
    authorized_users = {}

# Загрузка словаря кодов
with open(os.path.join(DATA_DIR, 'dict_with_codes.json'), 'r', encoding='utf-8') as f:
    auth_dict = json.load(f)

with open(os.path.join(DATA_DIR, 'players.json'), 'r', encoding='utf-8') as f:
    players_list = json.load(f)

if len(players_list) % 2 == 1:
    players_list += ['']

players_list_menu = [(players_list[name1],players_list[name2]) for name1, name2 in zip(range(0,len(players_list), 2), range(1,len(players_list), 2))]

# Прогнозы
forecast = {}

forecast_trigger = ['Прогноз', 'Сделать прогноз']
scores_types = ['0', '1', '2', '3', '4', '5', '6', '7', '8 и больше']
first_scored = ['Рома', 'Соперник', 'Так и не откроют счет']

# нотификация пользователей о запуске бота
try:
    with open(os.path.join(DATA_DIR, 'reboot_notifications.json'), 'r', encoding='utf-8') as f:
        reboot_notifications = json.load(f)
except:
    reboot_notifications = {}