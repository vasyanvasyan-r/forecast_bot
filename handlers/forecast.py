from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime as dt
from aiogram.types import FSInputFile


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
        #гифка
        animation_from_file = FSInputFile(path=f"utils/{control['m_id']}.mp4") # type: ignore
        await message.answer_animation(animation=animation_from_file)

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
    answer = message.text.strip()  # type: ignore
    assert answer is not None, "Сломался путь, пользователь оказался здесь случайно"
    if answer in tq['a']:

        await state.update_data(coach=message.text.strip()) # type: ignore

        await message.answer("Сколько забьет Рома в первом тайме?",
                            reply_markup = scores_menu('0'))
        await state.set_state(ForecastStates.roma_score_fh)
    else:

        await message.answer("Нет такого варианта, воспользуйтесь меню ввода",
                            reply_markup=tq_menu)
        await state.set_state(ForecastStates.temp_question)

# 1. Счёт первого тайма
@router.message(ForecastStates.roma_score_fh)
async def score_fh_roma_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_s_fh=int(message.text.strip()) if message.text.strip() != '8 и больше' else '8')

    await message.answer("Сколько пропустит Рома в первом тайме?",
                         reply_markup = scores_menu('0'))
    await state.set_state(ForecastStates.rival_score_fh)

@router.message(ForecastStates.rival_score_fh)
async def score_fh_opp_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_m_fh=int(message.text.strip()) if message.text.strip() != '8 и больше' else '8')
    prev_choice = (await state.get_data())['r_s_fh']
    await message.answer("Сколько Рома забьет за матч?",
                         reply_markup= scores_menu(str(prev_choice) if prev_choice != 8 else '8 и больше'))
    await state.set_state(ForecastStates.roma_score_ft)

# 2. Счёт полного матча
@router.message(ForecastStates.roma_score_ft)
async def score_ft_roma_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_s=int(message.text.strip()) if message.text.strip() != '8 и больше' else '8')
    prev_choice = (await state.get_data())['r_m_fh']
    await message.answer("Сколько Рома пропустит за матч", 
                         reply_markup=scores_menu(str(prev_choice) if prev_choice != 8 else '8 и больше'))

    await state.set_state(ForecastStates.rival_score_ft)

@router.message(ForecastStates.rival_score_ft)
async def score_ft_opp_handler(message: types.Message, state: FSMContext):
    assert message.text is not None
    await state.update_data(r_m=int(message.text.strip()) if message.text.strip() != '8 и больше' else '8')

    await message.answer("Кто забьёт голы за Рому?\n"
                         "Теперь ВАШИ ограничения доступны в скобочках \\(\\) напротив фамилии футболиста\n"
                         "То же самое, что в [таблице](https://docs.google.com/spreadsheets/d/1I7APxniANMu1r1y2uRGKDrLGuR4-OeUZDqvTtrn6vos/edit?gid=1025145962#gid=1025145962)"
                         "Если у вас стоит 0 в таблице, значит вы не сможете больше выбрать этого футболиста",
                         parse_mode="MarkdownV2",
                         reply_markup= ReplyKeyboardRemove())

    await state.set_state(ForecastStates.entering_scorers)
    await scorers_handler(message, state)

# 3. Автор голов
@router.message(ForecastStates.entering_scorers)
async def scorers_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    r_s, r_m = data['r_s'], int(data['r_m'])
    if r_s == scores_types[-1]:
        r_s = 8
    if int(r_s) == 0:
        await message.answer("Поскольку указали, что Рома не забьет, то и игроков не покажу, Вот ваш прогноз")
        await state.update_data(scorers=[])
        await state.update_data(assists=[])

        try:
            control = await get_control()
        except:
            print("Использую стартовую версию контрольного словаря")
        control = await update_time_in_control(control) # type: ignore

        if control['closed']:
            await state.clear()
            await message.answer(f"Прогнозы не принимаются. Меньше двух часов. Матч в {control['data']['date']}", 
                                reply_markup=auth_menu)
        else:        
            if r_m > 0:
                await state.update_data(first_scored=first_scored[1])
            else:
                await state.update_data(first_scored=first_scored[2])
            await state.update_data(timestamp=dt.now().strftime('%d-%m-%Y %H:%M:%S-%f'))
            data = await state.get_data()
            result = (
                f"✅ Ваш прогноз:\n"
                f"½ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} {control['data']['rival']}\n"
                f"⏱ Счёт матча: Рома {data['r_s']} -- {data['r_m']} {control['data']['rival']}\n"
                f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                f"🥅 Первый гол: {data['first_scored']}\n"
                f"❓ Временный вопрос: {data['coach']}"
            ) if control['data']['home'] == '1' else (
                f"✅ Ваш прогноз:\n"
                f"½ Счёт первого тайма:  {control['data']['rival']} {data['r_m_fh']} -- {data['r_s_fh']} Рома\n"
                f"⏱ Счёт матча: {control['data']['rival']} {data['r_m']} -- {data['r_s']} Рома\n"
                f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                f"🥅 Первый гол: {data['first_scored']}\n"
                f"❓ Временный вопрос: {data['coach']}"
            )
            await message.answer(result)
            assert message.from_user is not None
            forecast[authorized_users[message.from_user.id]] = data
            try:
                all_forecasts[authorized_users[message.from_user.id]] += [data]
            except:
                all_forecasts[authorized_users[message.from_user.id]] = [data]
            async with aiofiles.open(os.path.join(DATA_DIR, f'forecast_{control["m_id"]}.json'), mode="w") as f:
                await f.write(json.dumps(forecast, indent=4))
            async with aiofiles.open(os.path.join(PULL_DIR, "all_forecasts.json"), mode="w") as f:
                await f.write(json.dumps(all_forecasts, indent = 4))
            await state.clear()
            await message.answer("Прогноз записан", reply_markup=auth_menu)                  

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
        r_s = 8
    else:
        r_s = int(r_s)
    players_list = [k for k in players_dict]
    assert message.text is not None
    text = message.text.split(' (')[0]
    if authorized_users[message.from_user.id] in goals_restrict: # type: ignore
        drop_players = [k for k, v in goals_restrict[authorized_users[message.from_user.id]].items() if v == '0']  # type: ignore
    else:
        drop_players = []
    if text in players_list and text not in drop_players:
        
        inputs.append(text)
        i += 1
        if i <= r_s:
            await state.update_data(inputs=inputs, scorer_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
    elif message.text.lower() == "закончить ввод":                
        await message.answer("Понял, принял, записал")
    elif text in drop_players:
        await message.answer("У вас закончились возможности упомянуть этого футболиста, в списке перечислены все доступные футболисты. Воспользуйтесь списком.")
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
        r_s = 8
    else:
        r_s = int(r_s)

    players_list = [k for k in players_dict]
    assert message.text is not None
    text = message.text.split(' (')[0]
    
    if authorized_users[message.from_user.id] in assists_restrict: # type: ignore
        drop_players = [k for k, v in assists_restrict[authorized_users[message.from_user.id]].items() if v == '0']  # type: ignore
    else:
        drop_players = []
    if text in players_list and text not in drop_players:

        inputs.append(text)
        i += 1
        if i <= r_s:
            await state.update_data(inputs=inputs, assist_count=i)
        if i == r_s:
            await message.answer(f"Принято ({i}/{r_s}).")
        else:
            await message.answer(f"Принято ({i}/{r_s}). Ещё?")
    elif message.text.lower() == "закончить ввод":                
        await message.answer("Понял, принял, записал")
    elif text in drop_players:
        await message.answer("У вас закончились возможности упомянуть этого футболиста, в списке перечислены все доступные футболисты. Воспользуйтесь списком.")
    else:
        await message.answer("Нет такого футболиста, воспользуйтесь списком")
    
    if message.text.lower() == "закончить ввод" or i == r_s:

        await message.answer(f"Вы ввели {len(inputs)} авторов голевых передач, по именам:\n" + "\n".join(inputs))
        await state.update_data(assists=inputs)
        r_s_fh, r_m_fh, r_m = int(data['r_s_fh']), int(data['r_m_fh']), int(data['r_m'])
        cond_roma = (r_s > 0 and r_m == 0) or (r_s_fh > 0 and r_m_fh == 0)
        cond_rival = (r_s == 0 and r_m > 0) or (r_s_fh == 0 and r_m_fh > 0)
        try:
            control = await get_control()
        except:
            print("Использую стартовую версию контрольного словаря")
        if cond_roma:
            control = await update_time_in_control(control) # type: ignore

            if control['closed']:
                await state.clear()
                await message.answer(f"Прогнозы не принимаются. Меньше двух часов. Матч в {control['data']['date']}", 
                                    reply_markup=auth_menu)
            else:        

                await state.update_data(first_scored=first_scored[0])
                await state.update_data(timestamp=dt.now().strftime('%d-%m-%Y %H:%M:%S-%f'))
                data = await state.get_data()
                result = (
                    f"✅ Ваш прогноз:\n"
                    f"½ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} {control['data']['rival']}\n"
                    f"⏱ Счёт матча: Рома {data['r_s']} -- {data['r_m']} {control['data']['rival']}\n"
                    f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                    f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                    f"🥅 Первый гол: {data['first_scored']}\n"
                    f"❓ Временный вопрос: {data['coach']}"
                ) if control['data']['home'] == '1' else (
                    f"✅ Ваш прогноз:\n"
                    f"½ Счёт первого тайма:  {control['data']['rival']} {data['r_m_fh']} -- {data['r_s_fh']} Рома\n"
                    f"⏱ Счёт матча: {control['data']['rival']} {data['r_m']} -- {data['r_s']} Рома\n"
                    f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                    f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                    f"🥅 Первый гол: {data['first_scored']}\n"
                    f"❓ Временный вопрос: {data['coach']}"
                )
                await message.answer(result)
                assert message.from_user is not None
                forecast[authorized_users[message.from_user.id]] = data
                try:
                    all_forecasts[authorized_users[message.from_user.id]] += [data]
                except:
                    all_forecasts[authorized_users[message.from_user.id]] = [data]
                async with aiofiles.open(os.path.join(DATA_DIR, f'forecast_{control["m_id"]}.json'), mode="w") as f:
                    await f.write(json.dumps(forecast, indent=4))
                async with aiofiles.open(os.path.join(PULL_DIR, "all_forecasts.json"), mode="w") as f:
                    await f.write(json.dumps(all_forecasts, indent = 4))
                await state.clear()
                await message.answer("Прогноз записан", reply_markup=auth_menu)
        elif cond_rival:
            control = await update_time_in_control(control) # type: ignore

            if control['closed']:
                await state.clear()
                await message.answer(f"Прогнозы не принимаются. Меньше двух часов. Матч в {control['data']['date']}", 
                                    reply_markup=auth_menu)
            else:        

                await state.update_data(first_scored=first_scored[1])
                await state.update_data(timestamp=dt.now().strftime('%d-%m-%Y %H:%M:%S-%f'))
                data = await state.get_data()
                result = (
                    f"✅ Ваш прогноз:\n"
                    f"½ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} {control['data']['rival']}\n"
                    f"⏱ Счёт матча: Рома {data['r_s']} -- {data['r_m']} {control['data']['rival']}\n"
                    f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                    f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                    f"🥅 Первый гол: {data['first_scored']}\n"
                    f"❓ Временный вопрос: {data['coach']}"
                ) if control['data']['home'] == '1' else (
                    f"✅ Ваш прогноз:\n"
                    f"½ Счёт первого тайма:  {control['data']['rival']} {data['r_m_fh']} -- {data['r_s_fh']} Рома\n"
                    f"⏱ Счёт матча: {control['data']['rival']} {data['r_m']} -- {data['r_s']} Рома\n"
                    f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                    f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                    f"🥅 Первый гол: {data['first_scored']}\n"
                    f"❓ Временный вопрос: {data['coach']}"
                )
                await message.answer(result)
                assert message.from_user is not None
                forecast[authorized_users[message.from_user.id]] = data
                try:
                    all_forecasts[authorized_users[message.from_user.id]] += [data]
                except:
                    all_forecasts[authorized_users[message.from_user.id]] = [data]
                async with aiofiles.open(os.path.join(DATA_DIR, f'forecast_{control["m_id"]}.json'), mode="w") as f:
                    await f.write(json.dumps(forecast, indent=4))
                async with aiofiles.open(os.path.join(PULL_DIR, "all_forecasts.json"), mode="w") as f:
                    await f.write(json.dumps(all_forecasts, indent = 4))
                await state.clear()
                await message.answer("Прогноз записан", reply_markup=auth_menu)            
            
        else:
            await message.answer("Кто откроет счёт? (Рома / Соперник / Так и не откроют счет):", reply_markup=openning_menu)
            await state.set_state(ForecastStates.entering_first_goal)


# 5. Кто откроет счёт
#first_scored = ['Рома', 'Противник', 'Так и не откроют счет']
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
                f"½ Счёт первого тайма: Рома {data['r_s_fh']} -- {data['r_m_fh']} {control['data']['rival']}\n"
                f"⏱ Счёт матча: Рома {data['r_s']} -- {data['r_m']} {control['data']['rival']}\n"
                f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                f"🥅 Первый гол: {data['first_scored']}\n"
                f"❓ Временный вопрос: {data['coach']}"
            ) if control['data']['home'] == '1' else (
                f"✅ Ваш прогноз:\n"
                f"½ Счёт первого тайма:  {control['data']['rival']} {data['r_m_fh']} -- {data['r_s_fh']} Рома\n"
                f"⏱ Счёт матча: {control['data']['rival']} {data['r_m']} -- {data['r_s']} Рома\n"
                f"⚽️ Голы: {', '.join(data['scorers'])}\n"
                f"🎯 Ассисты: {', '.join(data['assists'])}\n"
                f"🥅 Первый гол: {data['first_scored']}\n"
                f"❓ Временный вопрос: {data['coach']}"
            )
            await message.answer(result)
            assert message.from_user is not None
            forecast[authorized_users[message.from_user.id]] = data
            try:
                all_forecasts[authorized_users[message.from_user.id]] += [data]
            except:
                all_forecasts[authorized_users[message.from_user.id]] = [data]
            async with aiofiles.open(os.path.join(DATA_DIR, f'forecast_{control["m_id"]}.json'), mode="w") as f:
                await f.write(json.dumps(forecast, indent=4))
            async with aiofiles.open(os.path.join(PULL_DIR, "all_forecasts.json"), mode="w") as f:
                await f.write(json.dumps(all_forecasts, indent = 4))
            await state.clear()
            await message.answer("Прогноз записан", reply_markup=auth_menu)
        else:
            await message.answer("Нет такого варианта, воспользуйтесь списком")


