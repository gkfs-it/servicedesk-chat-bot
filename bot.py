import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ACCESS_MODE
from handlers import start, ticket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задано в .env")

    logger.info("Запуск бота. Режим доступу: %s", ACCESS_MODE)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(ticket.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
