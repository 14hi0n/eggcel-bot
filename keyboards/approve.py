from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def approve_chat_keyboard(chat_id: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Одобрить", callback_data=f"chat:approved:{chat_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отклонить", callback_data=f"chat:rejected:{chat_id}"
                )
            ],
        ]
    )
