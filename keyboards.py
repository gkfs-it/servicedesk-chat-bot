from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Створити заявку", callback_data="create_ticket")]
    ])


def priority_keyboard(priorities: list[dict]) -> InlineKeyboardMarkup:
    """Будує клавіатуру з реальних пріоритетів SDP."""
    rows = []
    row = []
    for p in priorities:
        row.append(InlineKeyboardButton(
            text=p["name"],
            callback_data=f"priority_{p['id']}",
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def photos_keyboard(count: int, max_photos: int) -> InlineKeyboardMarkup:
    buttons = []
    if count > 0:
        buttons.append([InlineKeyboardButton(text=f"✅ Готово ({count} фото)", callback_data="photos_done")])
    buttons.append([InlineKeyboardButton(text="⏭ Пропустити", callback_data="photos_skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити та надіслати", callback_data="ticket_confirm")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="ticket_cancel")],
    ])
