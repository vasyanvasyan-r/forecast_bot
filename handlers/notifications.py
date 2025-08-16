from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from states.user_states import NotificationsStates
from utils.storage import authorized_users, notifications, reboot_notifications, DATA_DIR
from keyboards.menu import notifications_start_menu, start_menu, yes_no

import aiofiles
import json
import os

router = Router()

@router.message(StateFilter(None), lambda msg: msg.text == "Уведомления")
async def notifications_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id in authorized_users:
        if user_id in notifications:
            await message.answer(f"Выберете, какие настройки хотите изменить, "
                             f"{authorized_users[str(message.from_user.id)]}", 
                         reply_markup= notifications_start_menu)
            
        else:
            await message.answer(f"Выберете, какое уведомление отправлять, "
                             f"{authorized_users[str(message.from_user.id)]}", 
                         reply_markup= notifications_start_menu)
        await state.set_state(NotificationsStates.start_up_notification)
    else:
        await message.answer("Сначала надо авторизоваться", 
                         reply_markup= start_menu)


    

@router.message(NotificationsStates.start_up_notification)
async def ask_reboot_notifications(message: types.Message, state: FSMContext):
    await message.answer(f"Хотите получать уведомления о старте бота?",
                         reply_markup=yes_no)
    await state.set_state(NotificationsStates.seting_reboot_notifications)

@router.message(NotificationsStates.seting_reboot_notifications)
async def ask_reboot_notifications(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer == "Да":
        user_id = message.from_user.id
        reboot_notifications[user_id] = 'yes'
        notifications[user_id] = ['reboot']
        async with aiofiles.open(os.path.join(DATA_DIR, "reboot_notifications.json"), mode="w") as f:
            await f.write(json.dumps(reboot_notifications) + "\n")
        async with aiofiles.open(os.path.join(DATA_DIR, "notifications.json"), mode="w") as f:
            await f.write(json.dumps(notifications) + "\n")
    await message.answer(f"Хотите получать уведомления о старте бота?",
                         reply_markup=yes_no)
    await state.set_state(NotificationsStates.seting_reboot_notifications)    