from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime as dt


from states.user_states import ForecastStates, MultiInputStates
from utils.storage import authorized_users, \
    forecast, forecast_trigger, first_scored, scores_types,\
        DATA_DIR, PULL_DIR, get_control, tq, update_time_in_control, all_forecasts,\
        goals_restrict, assists_restrict, get_personal_list_of_players, players_dict
from keyboards.menu import auth_menu, scores_menu, openning_menu, start_menu, tq_menu, get_players_menu

import aiofiles
import json
import os


router = Router()

# Старт прогноза
@router.message(StateFilter(None), lambda message: message.text in forecast_trigger)
async def start_forecast(message: types.Message, state: FSMContext):
    assert message.from_user is not None
    user_id = message.from_user.id
    if user_id not in authorized_users:
        await message.answer("Сначала пройдите авторизацию.",
                              reply_markup=start_menu)
        return
    try:
        control = await get_control()
    except:
        print("Использую стартовую версию контрольного словаря")
    
    control = await update_time_in_control(control)
    print(f'==== {authorized_users[user_id]} делает прогноз переменная управления: \n {control}')
    if control['polling']:

        await message.answer(f"{tq['q']}",
                            reply_markup=tq_menu)
        await state.set_state(ForecastStates.temp_question)
    elif control['closed']:
        await message.answer("Прогнозы уже не принимаются",
                              reply_markup=start_menu)        
    elif control['waiting']:
        await message.answer("Прогнозы еще не принимаются",
                              reply_markup=start_menu)
    else:
        await message.answer("Неизвестная ошибка. Попробуйте еще раз.",
                              reply_markup=start_menu)

@router.message(ForecastStates.temp_question)
async def temp_q_parsing(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(coach=message.text.strip())

    await message.answer("Сколько забьет Рома в первом тайме?",
                         reply_markup = scores_menu('0'))
    await state.set_state(ForecastStates.roma_score_fh)
# 1. Счёт первого тайма
@router.message(ForecastStates.roma_score_fh)
async def score_fh_roma_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_s_fh=message.text.strip())

    await message.answer("Сколько пропустит Рома в первом тайме?",
                         reply_markup = scores_menu('0'))
    await state.set_state(ForecastStates.rival_score_fh)

@router.message(ForecastStates.rival_score_fh)
async def score_fh_opp_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_m_fh=message.text.strip())

    await message.answer("Сколько Рома забьет за матч?",
                         reply_markup= scores_menu((await state.get_data())['r_s_fh']))
    await state.set_state(ForecastStates.roma_score_ft)

# 2. Счёт полного матча
@router.message(ForecastStates.roma_score_ft)
async def score_ft_roma_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_s=message.text.strip())

    await message.answer("Сколько Рома пропустит за матч", 
                         reply_markup=scores_menu((await state.get_data())['r_m_fh']))

    await state.set_state(ForecastStates.rival_score_ft)

@router.message(ForecastStates.rival_score_ft)
async def score_ft_opp_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_m=message.text.strip())

    await message.answer("Кто забьёт голы за Рому?\n"
                         "Теперь ВАШИ ограничения доступны в скобочках \\(\\) напротив фамилии футболиста\n"
                         "То же самое, что в [таблице](https://docs.google.com/spreadsheets/d/1I7APxniANMu1r1y2uRGKDrLGuR4-OeUZDqvTtrn6vos/edit?gid=1025145962#gid=1025145962)",
                         parse_mode="MarkdownV2",
                         reply_markup= ReplyKeyboardRemove())

    await state.set_state(ForecastStates.entering_scorers)
    await scorers_handler(message, state)

# 3. Автор голов
@router.message(ForecastStates.entering_scorers)
async def scorers_handler(message: types.Message, state: FSMContext):
    r_s = (await state.get_data())['r_s']
    if r_s == scores_types[-1]:
        r_s = 100
    if int(r_s) == 0:
        await message.answer("Поскольку указали, что Рома не забьет, то и игроков не покажу, едем далее")
        await state.update_data(scorers=[])
        await state.update_data(assists=[])
        await message.answer("Кто откроет счёт? (Рома / Соперник / Так и не откроют счет):", reply_markup=openning_menu)
        await state.set_state(ForecastStates.entering_first_goal)
        await first_goal_handler(message, state)
    else:
        assert message.from_user is not None
        if authorized_users[message.from_user.id] in goals_restrict:

            await message.answer("Кто станет авторами голов?", reply_markup=
                                await get_players_menu(goals_restrict[authorized_users[
                                    message.from_user.id
                                ]]))
        else:
            await message.answer("Кто станет авторами голов?", reply_markup=
                                await get_players_menu({k:"13" for k in players_dict}))
        await state.set_state(MultiInputStates.waiting_inputs_scorers)
        await state.update_data(inputs=[]) 

    

@router.message(MultiInputStates.waiting_inputs_scorers)
async def collecting_scorers_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inputs = data.get("inputs", [])
    i = data.get("scorer_count", 0)  # достаём текущий счётчик
    r_s = data['r_s']
    if r_s == scores_types[-1]:
        r_s = 100
    else:
        r_s = int(r_s)
    players_list = [k for k in players_dict]
    assert message.text is not None
    text = message.text.split(' (')[0]
    if text in players_list:
        
        inputs.append(text)
        i += 1
        await state.update_data(inputs=inputs, scorer_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
    elif message.text.lower() == "закончить ввод":                
        await message.answer("Понял, принял, записал")
    else:
        await message.answer("Нет такого футболиста, воспользуйтесь списком")

    if message.text.lower() == "закончить ввод" or i == r_s:

        await message.answer(f"Вы ввели {len(inputs)} авторов голов:\n" + "\n".join(inputs))
        await state.update_data(scorers=inputs)
        assert message.from_user is not None
        if authorized_users[message.from_user.id] in assists_restrict:
            await message.answer("Кто отдаст голевые передачи?", reply_markup=
                                await get_players_menu(assists_restrict[authorized_users[
                                    
                                    message.from_user.id
                                ]]))
        else:
            await message.answer("Кто отдаст голевые передачи?", reply_markup=
                                await get_players_menu({k:"13" for k in players_dict}))            
        await state.set_state(MultiInputStates.waiting_inputs_assists)
        await state.update_data(inputs=[])
        return


# 4. Ассисты
@router.message(ForecastStates.entering_assists)
async def assists_handler(message: types.Message, state: FSMContext):
    assert message.from_user is not None
    if authorized_users[message.from_user.id] in assists_restrict:

        await message.answer("Кто отдаст голевые передачи?", reply_markup=
                            await get_players_menu(assists_restrict[authorized_users[
                                message.from_user.id
                            ]]))
    else:
        await message.answer("Кто отдаст голевые передачи?", reply_markup=
                            await get_players_menu({k:"13" for k in players_dict}))
        
    await state.set_state(MultiInputStates.waiting_inputs_assists)
    await state.update_data(inputs=[])
    
@router.message(MultiInputStates.waiting_inputs_assists)
async def collecting_assist_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inputs = data.get("inputs", [])
    i = data.get("assist_count", 0)  # достаём текущий счётчик
    r_s = data['r_s']
    if r_s == scores_types[-1]:
        r_s = 100
    else:
        r_s = int(r_s)

    players_list = [k for k in players_dict]
    assert message.text is not None
    text = message.text.split(' (')[0]
    if text in players_list:

        inputs.append(text)
        i += 1
        await state.update_data(inputs=inputs, assist_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
    elif message.text.lower() == "закончить ввод":                
        await message.answer("Понял, принял, записал")
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

    try:
        control = await get_control()
    except:
        print("Использую стартовую версию контрольного словаря")

    control = await update_time_in_control(control)

    if control['closed']:
        await state.clear()
        await message.answer(f"Прогнозы не принимаются. Меньше двух часов. Матч в {control['data']['date']}", 
                             reply_markup=auth_menu)
    else:        
        if message.text in first_scored:
            await state.update_data(first_scored=message.text.strip())
            await state.update_data(timestamp=dt.now().strftime('%d-%m-%Y %H:%M:%S-%f'))
            data = await state.get_data()
            result = (
                f"✅ Ваш прогноз:\n"
                f"▪ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} {control['data']['rival']}\n"
                f"▪ Счёт матча: Рома {data['r_s']} -- {data['r_m']} {control['data']['rival']}\n"
                f"▪ Голы: {data['scorers']}\n"
                f"▪ Ассисты: {data['assists']}\n"
                f"▪ Первый гол: {data['first_scored']}\n"
                f"▪ Временный вопрос: {data['coach']}"
            )
            await message.answer(result)
            assert message.from_user is not None
            forecast[authorized_users[message.from_user.id]] = data
            try:
                all_forecasts[authorized_users[message.from_user.id]] += [data]
            except:
                all_forecasts[authorized_users[message.from_user.id]] = [data]
            async with aiofiles.open(os.path.join(DATA_DIR, "forecasts.json"), mode="w") as f:
                await f.write(json.dumps(forecast, indent=4))
            async with aiofiles.open(os.path.join(PULL_DIR, "all_forecasts.json"), mode="w") as f:
                await f.write(json.dumps(all_forecasts, indent = 4))
            await state.clear()
            await message.answer("Прогноз записан", reply_markup=auth_menu)
        else:
            await message.answer("Нет такого варианта, воспользуйтесь списком")


