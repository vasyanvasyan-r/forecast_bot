import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from keys.config import TOKEN, TOKEN_TEST
from aiogram.types import ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from handlers import start, auth, forecast, notifications
from keyboards.menu import reboot_menu
from utils.storage import reboot_notifications, authorized_users

test = False
sendmessage = True
if not test:
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
else: 
    bot = Bot(token=TOKEN_TEST)
    dp = Dispatcher(storage=MemoryStorage())
# Регистрируем роутеры
dp.include_router(start.router)
dp.include_router(auth.router)
dp.include_router(forecast.router)
dp.include_router(notifications.router)


async def on_startup(bot: Bot):
    try:
        await bot.send_message(
                chat_id=166853396,
                text="✅ Бот запущен",
                reply_markup=reboot_menu
            )
    except Exception as e:
        print(f"Не удалось отправить master: {e}")
    if sendmessage:
        for user_id in authorized_users:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="""
                            Привет, наш дорогой Прогнозист\\!
Бот запущен и будет готов принять прогнозы на дерби против Лацио как только до матча останется меньше 2\\-х дней, то есть в 13\\-30 по Москве\\. 


Вот наш [Гайд](https://docs.google.com/document/d/1K7zAyX-6zEeMXGZAaAY59QjVyFsZpyNQgw1dZ4_dXBw/edit?tab=t.0)
Вот наши Таблицы [Прогнозиста](https://docs.google.com/spreadsheets/d/1I7APxniANMu1r1y2uRGKDrLGuR4-OeUZDqvTtrn6vos/edit?gid=1893944730#gid=1893944730)
Вот наш [Бусти](https://boosty.to/pro_asroma)\\. Будем рады, если поддержишь нас и поучаствуешь в Призовом фонде этого сезона\\. \\(Призовой фонд сейчас 1300 рублей\\)

❤️💛
                    """, 
                    parse_mode="MarkdownV2",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Сделать прогноз")]],
    resize_keyboard=True
)                    
                )
            except Exception as e:
                print(f"Не удалось отправить {user_id}: {e}")  

    for user_id in [key for key, value in reboot_notifications.items() if value == 'yes']:
        try:
            await bot.send_message(
                chat_id=user_id,
                text="✅ Бот запущен",
                reply_markup=reboot_menu
            )
        except Exception as e:
            print(f"Не удалось отправить {user_id}: {e}")
async def main():
    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
