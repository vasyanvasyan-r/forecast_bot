import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from keys.config import TOKEN, TOKEN_TEST

from handlers import start, auth, forecast, notifications
from keyboards.menu import reboot_menu
from utils.storage import reboot_notifications, authorized_users

test = True
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
                    text='Поздравляем с первой победой!\n'
                    'Выложили результаты матча и золотые баллы.\n'
                    'По поводу таблиц "Топ-10" и "Претенденты" обновление будет позднее. Хотим более подробно расписать как всё будет работать в этих таблицах и после этого обнародуем.\n'
                    'FORZA ROMA! ❤️💛\n\n'
                    'Бот тоже пойдет отдохнет)',
                    
                )
            except Exception as e:
                print(f"Не удалось отправить {user_id}: {e}")  
    if False:
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
