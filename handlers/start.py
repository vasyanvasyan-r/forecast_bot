from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import start_menu
from utils.storage import start_words
from aiogram.filters import StateFilter

from utils.storage import inprogress

router = Router()

@router.message(Command("start"))
@router.message(lambda message: message.text and message.text.lower() in start_words)
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот для прогнозов болельщиков AS Roma!",
                          reply_markup=start_menu)

# in progress
@router.message(StateFilter(None), lambda msg: msg.text in inprogress)
async def in_progress(message: types.Message):
    await message.answer(f"Будет доступно в будущих версиях",
                         reply_markup = start_menu)
