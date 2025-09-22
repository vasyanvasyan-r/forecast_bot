import json
import os

from datetime import datetime as dt
from datetime import timedelta as td

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
PULL_DIR = os.path.join(BASE_DIR, '..', 'pull_data')
print(PULL_DIR)


try:
    with open(os.path.join(BASE_DIR, 'control.json'), 'r', encoding='utf-8') as f:
        control = json.load(f)
    print('Загрузил контрольные переменные')
except:
    print("Не загрузил контроль")
# Авторизованные пользователи
try:
    with open(os.path.join(DATA_DIR, 'authorized_users.json'), 'r', encoding='utf-8') as f:
        authorized_users = json.load(f)
        authorized_users = {int(k): v for k, v in authorized_users.items()}
    print('Загрузил авторизованных юзеров')
except:
    authorized_users = {}

# Загрузка словаря кодов
with open(os.path.join(DATA_DIR, 'dict_with_codes.json'), 'r', encoding='utf-8') as f:
    auth_dict = json.load(f)
# загрузка игроков
with open(os.path.join(DATA_DIR, 'players.json'), 'r', encoding='utf-8') as f:
    players_list = json.load(f)
# заготовка для меню игроков
if len(players_list) % 2 == 1:
    players_list += ['']

players_list_menu = [(players_list[name1],players_list[name2]) for name1, name2 in zip(range(0,len(players_list), 2), range(1,len(players_list), 2))]
players_dict = {k:"13" for k in players_list}
def get_personal_list_of_players(search_dict, players_list_menu = players_list_menu):
    lst = [(i[0] + f" ({search_dict[i[0]]})" if i[0] in search_dict else i[0] + f" (13)",
            i[1] + f" ({search_dict[i[1]]})" if i[1] in search_dict else i[1] + f" (13)" if i[1] != "" else " (13)") 
            for i in players_list_menu]
    return lst
# Прогнозы
try:
    with open(os.path.join(DATA_DIR, f'forecast_{control["m_id"]}.json'), 'r', encoding='utf-8') as f:
        forecast = json.load(f)
        forecast = {int(k): v for k, v in forecast.items()}
except:
    forecast = {}

forecast_trigger = ['Прогноз', 'Сделать прогноз']
scores_types = ['0', '1', '2', '3', '4', '5', '6', '7', '8 и больше']
first_scored = ['Рома', 'Противник', 'Так и не откроют счет']

# нотификация пользователей о запуске бота
try:
    with open(os.path.join(DATA_DIR, 'reboot_notifications.json'), 'r', encoding='utf-8') as f:
        reboot_notifications = json.load(f)
        reboot_notifications = {int(k): v for k, v in reboot_notifications.items()}
except:
    reboot_notifications = {}
# прочая нотификация
try:
    with open(os.path.join(DATA_DIR, 'notifications.json'), 'r', encoding='utf-8') as f:
        notifications = json.load(f)
        notifications = {int(k): v for k, v in notifications.items()}
except:
    notifications = {}
# все прогнозы
try:
    with open(os.path.join(PULL_DIR, 'all_forecasts.json'), 'r', encoding='utf-8') as f:
        all_forecasts = json.load(f)
        all_forecasts = {str(k): v for k, v in all_forecasts.items()}
except:
    all_forecasts = {str(name): [] for name in authorized_users.values()}

start_words = [
    'начать',
    'в стартовое меню'
]

inprogress = ["Уведомления о старте/окончании приема прогнозов", 
              "Напоминалка",
              "Мои ачивки"]

try:
    with open(os.path.join(BASE_DIR, 'control.json'), 'r', encoding='utf-8') as f:
        control = json.load(f)
    print(control)
except Exception as e:
    print(f"Словарь контроля не считался"
          f"[{dt.now()}] ❌ Error: {e}")

try:
    with open(os.path.join(DATA_DIR, 'tq.json'), 'r', encoding='utf-8') as f:
        tq = json.load(f)
    print(tq)
except Exception as e:
    print(f"Временный не считался"
          f"[{dt.now()}] ❌ Error: {e}")
    
try:
    with open(os.path.join(DATA_DIR, 'goals_restrict.json'), 'r', encoding='utf-8') as f:
        goals_restrict = json.load(f)
    print(tq)
except Exception as e:
    print(f"Ограничение на голы не считался"
          f"[{dt.now()}] ❌ Error: {e}")

try:
    with open(os.path.join(DATA_DIR, 'assists_restrict.json'), 'r', encoding='utf-8') as f:
        assists_restrict = json.load(f)
    print(tq)
except Exception as e:
    print(f"Ограничение на ассисты не считался"
          f"[{dt.now()}] ❌ Error: {e}")

async def get_control(DIR = BASE_DIR):
    try:
        with open(os.path.join(DIR, 'control.json'), 'r', encoding='utf-8') as f:
            control = json.load(f)
    except Exception as e:
        print(f"Словарь контроля не считался"
            f"[{dt.now()}] ❌ Error: {e}")
    return control

async def update_time_in_control(control):
    control['waiting'] = dt.now() - (dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(days=2)) < td(0)
    control['polling'] = dt.now() - (dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(hours=2)) < td(0) and not control['waiting']
    control['closed'] = not control['waiting'] and not control ['polling']
    return control