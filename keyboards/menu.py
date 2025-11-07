from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.storage import players_list_menu, scores_types, tq,\
                            get_personal_list_of_players
# Стартовое меню
start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Авторизация"), KeyboardButton(text="Регистрация")],
        [KeyboardButton(text="Сделать прогноз"), KeyboardButton(text="Уведомления")]
    ],
    resize_keyboard=True
)
# После авторизации
auth_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сделать прогноз"), KeyboardButton(text="Мои ачивки"), KeyboardButton(text="Уведомления")]
    ],
    resize_keyboard=True
)
# сброс к предыдущему этапу
back_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)
# Авторы голов и голевых передач
players_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=f"{row[0]}"), KeyboardButton(text=f"{row[1]}")] for row in players_list_menu
    ] + [[KeyboardButton(text=f"Закончить ввод")]],
    resize_keyboard=True
)
tq_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=f"{option}")] for option in tq['a']],
    resize_keyboard=True
)

async def get_players_menu(search_dict):
    players_list_menu = get_personal_list_of_players(search_dict)
    players_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{row[0]}"), KeyboardButton(text=f"{row[1]}")] for row in players_list_menu
        ] + [[KeyboardButton(text=f"Закончить ввод")]],
        resize_keyboard=True)
    return players_menu
    

# Заготовка для голов
def scores_menu(prev_goals, scores_types = scores_types):
    i = scores_types.index(prev_goals)
    scores_types = scores_types[i:]
    if len(scores_types) % 2 == 1:
        scores_types += ['']

    scores_types_menu = [(scores_types[name1], scores_types[name2]) for name1, name2 in zip(range(0,len(scores_types), 2), range(1,len(scores_types), 2))]

    menu = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{row[0]}"), KeyboardButton(text=f"{row[1]}")] for row in scores_types_menu],
        resize_keyboard=True
    )
    
    return menu

# "Кто откроет счет -- меню"
openning_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Рома"), KeyboardButton(text="Противник")]
    ],
    resize_keyboard=True
)

reboot_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать")], [KeyboardButton(text="Отключить уведомления о старте бота")]
    ],
    resize_keyboard=True
)

notifications_start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Уведомления о старте бота")], 
        [KeyboardButton(text="Уведомления о старте/окончании приема прогнозов")],
        [KeyboardButton(text="Напоминалка")],
        [KeyboardButton(text="В стартовое меню")]
    ],
    resize_keyboard=True
)

yes_no = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")], [KeyboardButton(text="Нет")]
    ],
    resize_keyboard=True
)
