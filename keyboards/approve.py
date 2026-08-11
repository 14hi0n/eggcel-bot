from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def approve_chat_keyboard(chat_id: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Одобрить", callback_data=f"chat:approve:{chat_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отклонить", callback_data=f"chat:reject:{chat_id}"
                )
            ],
        ]
    )
