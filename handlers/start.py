import logging
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ACCESS_MODE, ACCESS_PASSWORD
from states import AccessFSM
from keyboards import main_menu_keyboard
from storage.auth import is_authenticated, authenticate

logger = logging.getLogger(__name__)
router = Router()


def _welcome_text(name: str) -> str:
    return (
        f"Вітаю, {name}! 👋\n\n"
        "Цей бот допоможе вам створити заявку в ServiceDesk Plus.\n\n"
        "Натисніть кнопку нижче, щоб розпочати."
    )


async def _grant_access(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = message.from_user.first_name or "Користувачу"
    await message.answer(_welcome_text(name), reply_markup=main_menu_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id

    if ACCESS_MODE == "restricted" and not is_authenticated(user_id):
        await message.answer(
            "🔐 Цей бот має обмежений доступ.\n\n"
            "Введіть код доступу:"
        )
        await state.set_state(AccessFSM.waiting_password)
        return

    await _grant_access(message, state)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer("❌ Дію скасовано.", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Немає активної дії.", reply_markup=main_menu_keyboard())


@router.message(AccessFSM.waiting_password)
async def check_password(message: Message, state: FSMContext) -> None:
    if not ACCESS_PASSWORD:
        logger.warning("ACCESS_PASSWORD не задано, доступ відхилено")
        await message.answer("⚠️ Помилка конфігурації. Зверніться до адміністратора.")
        return

    if message.text == ACCESS_PASSWORD:
        authenticate(message.from_user.id)
        logger.info("Користувач %d успішно автентифікований", message.from_user.id)
        await message.answer("✅ Доступ надано!")
        await _grant_access(message, state)
    else:
        await message.answer("❌ Невірний код доступу. Спробуйте ще раз:")
