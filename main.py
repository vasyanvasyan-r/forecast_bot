import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN

from handlers import start, auth, forecast, notifications
from keyboards.menu import reboot_menu
from utils.storage import reboot_notifications


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем роутеры
dp.include_router(start.router)
dp.include_router(auth.router)
dp.include_router(forecast.router)
dp.include_router(notifications.router)

test = False
async def on_startup(bot: Bot):
    if not test:
        try:
            await bot.send_message(
                    chat_id=166853396,
                    text="✅ Бот запущен",
                    reply_markup=reboot_menu
                )
        except Exception as e:
            print(f"Не удалось отправить {user_id}: {e}")
        for user_id in reboot_notifications:
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
