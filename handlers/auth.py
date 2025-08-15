from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from states.user_states import AuthStates
import aiofiles

import json


from keyboards.menu import auth_menu 
from utils.storage import auth_dict, authorized_users

router = Router()

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
        await message.answer("✅ Авторизация успешна!", reply_markup=auth_menu)
        async with aiofiles.open("authorized_users.json", mode="w") as f:
            await f.write(json.dumps(authorized_users) + "\n")
        await state.clear()
    else:
        await message.answer("❌ Неверное кодовое слово. Попробуйте снова:")
