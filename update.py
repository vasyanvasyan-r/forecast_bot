import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials  # <-- вместо oauth2client

# API credentials
path_to_credential = 'keys/credentials.json'
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# Создаём объект Credentials
credentials = Credentials.from_service_account_file(
    path_to_credential,
    scopes=scope
)

from datetime import datetime as dt
from datetime import timedelta as td
from functools import wraps
import time
import json
import os

# Авторизация gspread
try:
    gs = gspread.authorize(credentials)
except Exception as e:
    print(f"Не удалось авторизоваться в GoogleAPI, error: {e}")

# Подгрузка таблиц
try:
    control = gs.open('Данные')
    matches = control.worksheet("матчи")
    result_m = control.worksheet("результаты")
    temp_question = control.worksheet("временный вопрос")
    players = control.worksheet("игроки")
    gp_logs = control.worksheet("логи золотых баллов")
    print("Данные загружены")
except Exception as e:
    print(f"Не удалось подключтся к таблицам, error: {e}")
 



try:
    results = gs.open('Чемпионат прогнозистов 25/26')
    goals_restrict = results.worksheet("Доступные авторы голов")
    assists_restrict = results.worksheet("Доступные авторы ГП")
except Exception as e:
    print(f"Не удалось подключтся к таблицам, error: {e}")
# пути в нужные директории
ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT_DIR, "data")
PULL_DATA_DIR = os.path.join(ROOT_DIR, "pull_data")
UTILS_DIR = os.path.join(ROOT_DIR, "utils")

# функции для парсинга из таблицы данные
def fetch_data(sheet):
    # получим дата фрейм
    data = sheet.get_all_values()
    return pd.DataFrame(data, columns = data.pop(0))
def get_control(df):
    control = {}
    control['m_id'] = df.loc[[dt.strptime(i, "%d.%m.%Y %H:%M") > dt.now() for i in df.date] ,'match_id'].min()
    control['data'] = df.loc[int(control['m_id']), ['date', 'rival', 'home']].to_dict()
    control['waiting'] = dt.now() - (dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(days=2)) < td(0)
    control['polling'] = dt.now() - (dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(hours=2)) < td(0) and not control['waiting']
    control['closed'] = not control['waiting'] and not control ['polling']
    return control
    
def save_data(data, name, dir):
    FILE_PATH = os.path.join(dir, f"{name}.json")
    tmp_file = FILE_PATH + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_file, FILE_PATH)  # атомарная замена

from functools import wraps

def retry_on_exception(wait_sec=60, max_attempts=None):
    """
    Декоратор: повторяет выполнение функции при ошибке.
    
    :param wait_sec: сколько ждать между попытками
    :param max_attempts: максимум попыток, None = бесконечно
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    attempts += 1
                    print(f"[{dt.now()}] ❌ Error: {e} === Перерыв на {wait_sec} секунд ===")
                    if max_attempts and attempts >= max_attempts:
                        raise
                    time.sleep(wait_sec)
        return wrapper
    return decorator

#
parsing = True
while parsing:
    try:
        l_players = fetch_data(players).iloc[:, 0].to_list()
        print("Игроки скачались")
        parsing = False
    except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}"
              "=== Перерыв на минуту ===")
        time.sleep(60)

parsing = True
while parsing:
    try:
        m_df = fetch_data(matches)
        print("Матчи скачались")
        parsing = False
    except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}"
              "=== Перерыв на минуту ===")
        time.sleep(60)
control = get_control(m_df)

parsing = True
while parsing:
    try:
        tq = fetch_data(temp_question)
        tq = {'q': tq.loc[int(control['m_id']), 'question'],
            'a': tq.loc[int(control['m_id']), 'answers'].split(', ')}  # type: ignore
        print("Временный вопрос скачался")
        parsing = False
    except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}"
              "=== Перерыв на минуту ===")
        time.sleep(60)
# control and players

parsing = True
while parsing:
    try:
        df = fetch_data(goals_restrict)
        goals_restrict = df.set_index(df.columns.to_list()[0]).rename_axis(None, axis = 0).T.to_dict()
        df = fetch_data(assists_restrict)
        assists_restrict = df.set_index(df.columns.to_list()[0]).rename_axis(None, axis = 0).T.to_dict()
        print("Ограничения скачались")
        parsing = False
    except Exception as e:
        print(f"[{dt.now()}] ❌ Игроки Error: {e}"
              "=== Перерыв на минуту ===")
        time.sleep(60)


try:
    save_data(l_players, 'players', DATA_DIR)
    print("Игроки записались")
    save_data(tq, 'tq', DATA_DIR)
    print("Временный вопрос записался")    
    save_data(control, 'control', UTILS_DIR)
    print("Контроль записан")
    save_data(goals_restrict, 'goals_restrict', DATA_DIR)
    print("Ограничение на голы записалось")
    save_data(assists_restrict, 'assists_restrict', DATA_DIR)
    print("Ограничение на ассисты записалось")   

except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}")

print(get_control(m_df))




def main():
    while True:
        try:
            time.sleep(60*60)

            save_data(get_control(m_df), 'control', UTILS_DIR)
            print(f"[{dt.now()}] ✅ Control updated")
        except Exception as e:
            print(f"[{dt.now()}] ❌ Error: {e}")
        time.sleep(60*60)  # спим 1 час

if __name__ == "__main__":
    main()
