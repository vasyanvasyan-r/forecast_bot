from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove
import aiofiles

import json
import os

from states.user_states import AuthStates
from keyboards.menu import auth_menu
from utils.storage import auth_dict, authorized_users, DATA_DIR, all_forecasts

router = Router()

@router.message(StateFilter(None), lambda msg: msg.text == "Регистрация")
async def ask_for_agreement(message: types.Message, state: FSMContext):
    if message.from_user.id in list(authorized_users.keys()):
        await message.answer(f"Вы уже авторизованы как "
                             f"{authorized_users[message.from_user.id]}", 
                         reply_markup = auth_menu)
    else:
        await message.answer("Придумайте себе ник!", 
                         reply_markup= ReplyKeyboardRemove())

        await state.set_state(AuthStates.reg_nick)

@router.message(AuthStates.reg_nick)
async def new_nick(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if nickname in auth_dict:
        await message.answer("Такой ник уже существует, придумай другой")
    else:
        await state.update_data(nickname=nickname)
        await message.answer(f"Окей, {nickname} теперь придумай кодовое слово")
        await state.set_state(AuthStates.reg_code_word)

@router.message(AuthStates.reg_code_word)
async def new_nick(message: types.Message, state: FSMContext):
    word = message.text.strip()
    nickname = (await state.get_data())['nickname']
    auth_dict[nickname] = word
    async with aiofiles.open(os.path.join(DATA_DIR, "dict_with_codes.json"), mode="w") as f:
        await f.write(json.dumps(auth_dict) + "\n") 
    await message.answer(f"Окей {word} твое кодовое слово. Я его записал. "
                         "Запомни его, с помощью него можно авторизоваться. "
                         "Мы, конечно, после авторизации запомним тебя, но всякое может быть)"
                         f"\n {nickname}, Введи еще раз кодовое слово, чтобы авторизоваться.")
    await state.set_state(AuthStates.waiting_for_password)

@router.message(StateFilter(None), lambda msg: msg.text == "Авторизация")
async def ask_nickname(message: types.Message, state: FSMContext):
    if message.from_user.id in authorized_users:
        await message.answer(f"Вы уже авторизованы как {authorized_users[message.from_user.id]}")
    else:
        await message.answer("Введите никнейм:")
        await state.set_state(AuthStates.waiting_for_nickname)

@router.message(AuthStates.waiting_for_nickname)
async def get_nickname(message: types.Message, state: FSMContext):

    nickname = message.text.strip()
    await state.update_data(nickname=nickname)
    if nickname in auth_dict:
        await message.answer("Введите кодовое слово:")
        await state.set_state(AuthStates.waiting_for_password)
    else:
        await message.answer("Нет такого ника в базе!")

@router.message(AuthStates.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nickname = data["nickname"]
    password = message.text.strip()

    if auth_dict.get(nickname) == password:
        authorized_users[message.from_user.id] = nickname
        all_forecasts[nickname] = []
        await message.answer("✅ Авторизация успешна!", reply_markup=auth_menu)
        async with aiofiles.open(os.path.join(DATA_DIR, "authorized_users.json"), mode="w") as f:
            await f.write(json.dumps(authorized_users) + "\n")
        await state.clear()
    else:
        await message.answer("❌ Неверное кодовое слово. Попробуйте снова:")
