from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def approve_chat_keyboard(
    chat_id: int,
    *,
    chat_url: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if chat_url is not None:
        rows.append(
            [InlineKeyboardButton(text="Открыть чат", url=chat_url)]
        )

    rows.extend(
        (
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
        )
    )

    return InlineKeyboardMarkup(rows)
