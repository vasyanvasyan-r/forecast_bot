import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
#API creditails
path_to_credential = 'keys/credentials.json'
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(path_to_credential, scope)

from datetime import datetime as dt
from datetime import timedelta as td

import time
import json
import os

try:
    gs = gspread.authorize(credentials)
except Exception as e:
    print(f"Не удалось авторизоваться в GoogleAPI, error: {e}")
try:
    # подгрузим таблицы из Данный и Чемпионат прогнозистов
    control = gs.open('Данные')
    matches = control.worksheet("матчи")
    result_m = control.worksheet("результаты")
    temp_question = control.worksheet("временный вопрос")
    players = control.worksheet("игроки")
    gp_logs = control.worksheet("логи золотых баллов")
    print("Данные загружены")
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
    control['waiting'] = dt.now() - dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(days=2) > td(0)
    control['polling'] = dt.now() - dt.strptime(control['data']['date'], "%d.%m.%Y %H:%M") - td(hours=2) < td(0) and not control['waiting']
    control['closed'] = not control['waiting'] and not control ['polling']
    return control
    
def save_data(data, name, dir):
    FILE_PATH = os.path.join(dir, f"{name}.json")
    tmp_file = FILE_PATH + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, FILE_PATH)  # атомарная замена

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
        tq = {'q': tq.loc[int(control['m_id']), 'question']}
        print("Временный вопрос скачался")
        parsing = False
    except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}"
              "=== Перерыв на минуту ===")
        time.sleep(60)
# control and players

try:
    save_data(l_players, 'players', DATA_DIR)
    print("Игроки записались")
    save_data(tq, 'tq', DATA_DIR)
    print("Временный вопрос записался")    
    save_data(control, 'control', UTILS_DIR)
    print("Контроль записан")
except Exception as e:
        print(f"[{dt.now()}] ❌ Error: {e}")

print(get_control(m_df))


def main():
    while True:
        try:
            save_data(get_control(m_df), 'control', ROOT_DIR)
            print(f"[{dt.now()}] ✅ Control updated")
        except Exception as e:
            print(f"[{dt.now()}] ❌ Error: {e}")
        time.sleep(600)  # спим 10 минут

if __name__ == "__main__":
    main()
