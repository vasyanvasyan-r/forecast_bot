from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime as dt
from datetime import timedelta as td

from states.user_states import ForecastStates
from utils.storage import authorized_users, forecast, players_list, forecast_trigger, first_scored, DATA_DIR
from keyboards.menu import auth_menu, players_menu, scores_menu, openning_menu, start_menu

import aiofiles
import json
import os

class MultiInputStates(StatesGroup):
    waiting_inputs_scorers = State()
    waiting_inputs_assists = State()

router = Router()

# Старт прогноза
@router.message(StateFilter(None), lambda message: message.text in forecast_trigger)
async def start_forecast(message: types.Message, state: FSMContext):
    if message.from_user.id not in authorized_users:
        await message.answer("Сначала пройдите авторизацию.",
                              reply_markup=start_menu)
        return

    await message.answer("Сколько Рома забьет в первом тайме?",
                         reply_markup=scores_menu('0'))
    await state.set_state(ForecastStates.roma_score_fh)

# 1. Счёт первого тайма
@router.message(ForecastStates.roma_score_fh)
async def score_fh_roma_handler(message: types.Message, state: FSMContext):
    await state.update_data(r_s_fh=message.text.strip())

    await message.answer("Сколько пропустит Рома в первом тайме?",
                         reply_markup = scores_menu('0'))
    await state.set_state(ForecastStates.rival_score_fh)

@router.message(ForecastStates.rival_score_fh)
async def score_fh_opp_handler(message: types.Message, state: FSMContext):
    await state.update_data(r_m_fh=message.text.strip())

    await message.answer("Сколько Рома забьет за матч?",
                         reply_markup= scores_menu((await state.get_data())['r_s_fh']))
    await state.set_state(ForecastStates.roma_score_ft)

# 2. Счёт полного матча
@router.message(ForecastStates.roma_score_ft)
async def score_ft_roma_handler(message: types.Message, state: FSMContext):
    await state.update_data(r_s=message.text.strip())

    await message.answer("Сколько Рома пропустит за матч", 
                         reply_markup=scores_menu((await state.get_data())['r_m_fh']))

    await state.set_state(ForecastStates.rival_score_ft)

@router.message(ForecastStates.rival_score_ft)
async def score_ft_opp_handler(message: types.Message, state: FSMContext):
    await state.update_data(r_m=message.text.strip())

    await message.answer("Кто забьёт голы за Рому?", 
                         reply_markup= ReplyKeyboardRemove())

    await state.set_state(ForecastStates.entering_scorers)
    await scorers_handler(message, state)

# 3. Автор голов
@router.message(ForecastStates.entering_scorers)
async def scorers_handler(message: types.Message, state: FSMContext):
    if int((await state.get_data())['r_s']) == 0:
        await message.answer("Поскольку указали, что Рома не забьет, то и каличей указывать не надо")
        await state.update_data(scorers=[])
        await state.update_data(assists=[])
        await message.answer("Кто откроет счёт? (Рома / Соперник / Так и не откроют счет):", reply_markup=openning_menu)
        await state.set_state(ForecastStates.entering_first_goal)
        await first_goal_handler(message, state)
    else:
        await message.answer("Введите авторов голов", reply_markup=players_menu)
        await state.set_state(MultiInputStates.waiting_inputs_scorers)
        await state.update_data(inputs=[]) 

    

@router.message(MultiInputStates.waiting_inputs_scorers)
async def collecting_scorers_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inputs = data.get("inputs", [])
    i = data.get("scorer_count", 0)  # достаём текущий счётчик
    r_s = int(data['r_s'])

    if message.text in players_list:
        
        inputs.append(message.text)
        i += 1
        await state.update_data(inputs=inputs, scorer_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
        
    else:
        await message.answer("Нет такого футболиста, воспользуйтесь списком")

    if message.text.lower() == "закончить ввод" or i == r_s:

        await message.answer(f"Вы ввели {len(inputs)} авторов голов:\n" + "\n".join(inputs))
        await state.update_data(scorers=inputs)
        await message.answer("Кто отдаст голевые передачи?", reply_markup=players_menu)
        await state.set_state(ForecastStates.entering_assists)
        await assists_handler(message, state)
        return


# 4. Ассисты
@router.message(ForecastStates.entering_assists)
async def assists_handler(message: types.Message, state: FSMContext):
    await message.answer("Введите авторов голевых передач", reply_markup=players_menu)
    await state.set_state(MultiInputStates.waiting_inputs_assists)
    await state.update_data(inputs=[])
    
@router.message(MultiInputStates.waiting_inputs_assists)
async def collecting_assist_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inputs = data.get("inputs", [])
    i = data.get("assist_count", 0)  # достаём текущий счётчик
    r_s = int(data['r_s'])

    if message.text in players_list:

        inputs.append(message.text)
        i += 1
        await state.update_data(inputs=inputs, assist_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
    else:
        await message.answer("Нет такого футболиста, воспользуйтесь списком")
    
    if message.text.lower() == "закончить ввод" or i == r_s:

        await message.answer(f"Вы ввели {len(inputs)} авторов голевых передач, по именам:\n" + "\n".join(inputs))
        
        await state.update_data(assists=inputs)
        await message.answer("Кто откроет счёт? (Рома / Соперник / Так и не откроют счет):", reply_markup=openning_menu)
        await state.set_state(ForecastStates.entering_first_goal)

# 5. Кто откроет счёт
@router.message(ForecastStates.entering_first_goal)
async def first_goal_handler(message: types.Message, state: FSMContext):
    if message.text in first_scored:
        await state.update_data(first_scored=message.text.strip())
        await state.update_data(timestamp=dt.now().strftime('%d-%m-%Y %H:%M:%S-%f'))
        data = await state.get_data()
        result = (
            f"✅ Ваш прогноз:\n"
            f"▪ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} Противник\n"
            f"▪ Счёт матча: Рома {data['r_s']} -- {data['r_m']} Противник\n"
            f"▪ Голы: {data['scorers']}\n"
            f"▪ Ассисты: {data['assists']}\n"
            f"▪ Первый гол: {data['first_scored']}"
        )
        await message.answer(result)

        forecast[authorized_users[message.from_user.id]] = data
        async with aiofiles.open(os.path.join(DATA_DIR, "forecasts.json"), mode="w") as f:
            await f.write(json.dumps(forecast) + "\n")
        await state.clear()
        await message.answer("Прогноз записан", reply_markup=auth_menu)
    else:
        await message.answer("Нет такого варианта, воспользуйтесь списком")


