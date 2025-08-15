from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import start_menu

router = Router()

@router.message(Command("start"))
@router.message(lambda message: message.text and message.text.lower() == "начать")
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот для прогнозов болельщиков AS Roma!",
                          reply_markup=start_menu)
