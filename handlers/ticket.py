import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import MAX_PHOTOS, ACCESS_MODE
from states import TicketFSM
from keyboards import priority_keyboard, photos_keyboard, confirm_keyboard, main_menu_keyboard
from services.sdp_api import create_request, find_requester_id, get_priorities, upload_attachment
from storage.auth import is_authenticated

logger = logging.getLogger(__name__)
router = Router()


def _check_access(user_id: int) -> bool:
    if ACCESS_MODE == "restricted":
        return is_authenticated(user_id)
    return True


@router.callback_query(F.data == "create_ticket")
async def start_ticket(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_access(callback.from_user.id):
        await callback.answer("Доступ заборонено. Введіть /start", show_alert=True)
        return

    await callback.message.answer(
        "📋 <b>Створення нової заявки</b>\n\n"
        "Крок 1/4 — Введіть ваш <b>email</b> (як у ServiceDesk):\n"
        "<i>Наприклад: ivanov@company.ua</i>\n"
        "<i>(або /cancel для скасування)</i>",
        parse_mode="HTML",
    )
    await state.set_state(TicketFSM.waiting_login)
    await callback.answer()


@router.message(TicketFSM.waiting_login)
async def get_login(message: Message, state: FSMContext) -> None:
    login = message.text.strip()
    if not login:
        await message.answer("⚠️ Логін не може бути порожнім. Введіть ще раз:")
        return
    if len(login) > 100:
        await message.answer("⚠️ Логін занадто довгий (максимум 100 символів). Введіть ще раз:")
        return

    await state.update_data(login=login)
    await message.answer(
        "Крок 2/4 — Введіть <b>тему заявки</b>:",
        parse_mode="HTML",
    )
    await state.set_state(TicketFSM.waiting_subject)


@router.message(TicketFSM.waiting_subject)
async def get_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()
    if not subject:
        await message.answer("⚠️ Тема не може бути порожньою. Введіть ще раз:")
        return
    if len(subject) > 250:
        await message.answer("⚠️ Тема занадто довга (максимум 250 символів). Введіть ще раз:")
        return

    await state.update_data(subject=subject)
    await message.answer(
        "Крок 3/4 — Введіть <b>опис проблеми</b>:",
        parse_mode="HTML",
    )
    await state.set_state(TicketFSM.waiting_description)


@router.message(TicketFSM.waiting_description)
async def get_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if not description:
        await message.answer("⚠️ Опис не може бути порожнім. Введіть ще раз:")
        return
    if len(description) > 4000:
        await message.answer("⚠️ Опис занадто довгий (максимум 4000 символів). Введіть ще раз:")
        return

    await state.update_data(description=description)

    try:
        priorities = await get_priorities()
    except Exception:
        logger.exception("Не вдалося завантажити пріоритети з SDP")
        priorities = []

    if not priorities:
        await message.answer(
            "⚠️ Не вдалося отримати список пріоритетів із ServiceDesk.\n"
            "Спробуйте пізніше або зверніться до адміністратора."
        )
        return

    await state.update_data(priorities=priorities)
    await message.answer(
        "Крок 4/4 — Оберіть <b>пріоритет заявки</b>:",
        reply_markup=priority_keyboard(priorities),
        parse_mode="HTML",
    )
    await state.set_state(TicketFSM.waiting_priority)


@router.callback_query(TicketFSM.waiting_priority, F.data.startswith("priority_"))
async def get_priority(callback: CallbackQuery, state: FSMContext) -> None:
    priority_id = callback.data.split("_", 1)[1]
    data = await state.get_data()

    # Знаходимо назву пріоритету зі збереженого списку
    priorities = data.get("priorities", [])
    priority_name = next(
        (p["name"] for p in priorities if str(p["id"]) == priority_id),
        priority_id,
    )

    await state.update_data(priority=priority_name, photos=[])

    await callback.message.answer(
        f"Пріоритет: <b>{priority_name}</b>\n\n"
        f"📷 Надішліть фото до заявки (до {MAX_PHOTOS} шт.)\n"
        "Або натисніть <b>«Пропустити»</b>, якщо фото не потрібні.",
        reply_markup=photos_keyboard(0, MAX_PHOTOS),
        parse_mode="HTML",
    )
    await state.set_state(TicketFSM.waiting_photos)
    await callback.answer()


@router.message(TicketFSM.waiting_photos, F.photo)
async def get_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos: list = data.get("photos", [])

    if len(photos) >= MAX_PHOTOS:
        await message.answer(
            f"⚠️ Досягнуто максимум {MAX_PHOTOS} фото.\n"
            "Натисніть «✅ Готово» для продовження.",
            reply_markup=photos_keyboard(len(photos), MAX_PHOTOS),
        )
        return

    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    remaining = MAX_PHOTOS - len(photos)
    if remaining > 0:
        await message.answer(
            f"📷 Фото {len(photos)} додано. Можна додати ще {remaining}.",
            reply_markup=photos_keyboard(len(photos), MAX_PHOTOS),
        )
    else:
        await message.answer(
            f"📷 Фото {len(photos)} додано. Досягнуто ліміт.",
            reply_markup=photos_keyboard(len(photos), MAX_PHOTOS),
        )


@router.message(TicketFSM.waiting_photos)
async def photos_wrong_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    await message.answer(
        "Надішліть фото або натисніть кнопку нижче.",
        reply_markup=photos_keyboard(len(photos), MAX_PHOTOS),
    )


@router.callback_query(TicketFSM.waiting_photos, F.data.in_({"photos_done", "photos_skip"}))
async def finish_photos(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    priority_label = data.get("priority", "")
    photos_text = f"{len(photos)} фото" if photos else "без фото"

    summary = (
        "📋 <b>Підсумок заявки:</b>\n\n"
        f"👤 <b>Email:</b> {data['login']}\n"
        f"📌 <b>Тема:</b> {data['subject']}\n"
        f"📝 <b>Опис:</b> {data['description']}\n"
        f"🎯 <b>Пріоритет:</b> {priority_label}\n"
        f"📷 <b>Вкладення:</b> {photos_text}\n\n"
        "Підтвердити відправку заявки?"
    )

    await callback.message.answer(summary, reply_markup=confirm_keyboard(), parse_mode="HTML")
    await state.set_state(TicketFSM.confirming)
    await callback.answer()


@router.callback_query(TicketFSM.confirming, F.data == "ticket_confirm")
async def confirm_ticket(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    await callback.answer()

    status_msg = await callback.message.answer("⏳ Шукаю користувача в ServiceDesk...")

    try:
        requester_id = await find_requester_id(data["login"])
    except Exception as e:
        logger.exception("Помилка пошуку requester")
        await status_msg.edit_text(
            f"❌ Не вдалося з'єднатися з ServiceDesk: {e}\n"
            "Спробуйте пізніше або зверніться до адміністратора."
        )
        return

    if not requester_id:
        await status_msg.edit_text(
            f"❌ Користувача з email <b>{data['login']}</b> не знайдено в ServiceDesk.\n\n"
            "Перевірте email або зверніться до адміністратора — "
            "можливо, акаунт ще не створено.",
            parse_mode="HTML",
        )
        await callback.message.answer(
            "Спробувати ще раз або скасувати?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await status_msg.edit_text("⏳ Створюю заявку...")

    try:
        result = await create_request(
            requester_id=requester_id,
            subject=data["subject"],
            description=data["description"],
            priority=data["priority"],
        )
    except Exception as e:
        logger.exception("Помилка API SDP при створенні заявки")
        await status_msg.edit_text(
            f"❌ Не вдалося з'єднатися з ServiceDesk: {e}\n"
            "Спробуйте пізніше або зверніться до адміністратора."
        )
        return

    request_obj = result.get("request", {})
    request_id = request_obj.get("id")
    request_no = request_obj.get("display_id") or request_id

    if not request_id:
        error_msg = result.get("response_status", {}).get("message", str(result))
        await status_msg.edit_text(
            f"❌ Помилка при створенні заявки:\n{error_msg}"
        )
        return

    photos = data.get("photos", [])
    failed_uploads = 0

    for i, file_id in enumerate(photos, 1):
        try:
            file_io = await bot.download(file_id)
            await upload_attachment(str(request_id), file_io.read(), f"photo_{i}.jpg")
        except Exception:
            logger.exception("Не вдалося завантажити фото %d для заявки %s", i, request_id)
            failed_uploads += 1

    lines = [f"✅ Заявку <b>#{request_no}</b> успішно створено!"]
    if photos:
        uploaded = len(photos) - failed_uploads
        if failed_uploads == 0:
            lines.append(f"📷 Додано фото: {len(photos)}")
        else:
            lines.append(f"⚠️ Завантажено фото: {uploaded} з {len(photos)}")

    await status_msg.edit_text("\n".join(lines), parse_mode="HTML")
    await callback.message.answer("Що бажаєте зробити далі?", reply_markup=main_menu_keyboard())


@router.callback_query(TicketFSM.confirming, F.data == "ticket_cancel")
async def cancel_ticket(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("❌ Заявку скасовано.", reply_markup=main_menu_keyboard())
    await callback.answer()
