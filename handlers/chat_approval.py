import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from helpers.telegram import get_text_callback
from keyboards.approve import approve_chat_keyboard
from services.admin_notifier import AdminNotifier
from services.chat_service import ChatActionOutcome, ChatService
from services.exceptions.chat_service import ChatNotFoundError
from texts.messages import AdminMessages

logger = logging.getLogger(__name__)


async def chat_moderate_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    callback = get_text_callback(update)

    if callback is None:
        return

    query, message, data = callback

    user = update.effective_user

    if user is None or user.id not in settings.admin_ids:
        await query.answer("Недостаточно прав", show_alert=True)
        return

    try:
        _, new_status_raw, chat_id_raw = data.split(":")
        new_status = ChatStatus(new_status_raw)
        chat_id = int(chat_id_raw)
    except ValueError, TypeError:
        logger.warning("Invalid callback data: %s", data)
        await query.answer("Что-то не то. Смотри логи", show_alert=True)
        return

    logger.info(f"Нажал на {new_status_raw} в контексте id: {chat_id_raw}")

    db: DatabaseManager = context.bot_data["db"]

    try:
        async with db.session_factory() as session, session.begin():
            repo = ChatRepository(session=session)
            service = ChatService(chat_repo=repo)

            result = await service.moderate_pending(
                chat_id=chat_id,
                new_status=new_status,
            )
    except ChatNotFoundError:
        logger.warning("Chat %s was not found in the database", chat_id)
        await query.answer("Чат не найден в БД", show_alert=True)
        return

    current_status = result.chat.status.value

    match result.outcome:
        case ChatActionOutcome.CHANGED:
            verdict = f"Статус: {current_status}"
            answer = "Статус изменен"
            alert = False

        case ChatActionOutcome.ALREADY_RESOLVED:
            verdict = f"Заявка уже обработана\nТекущий статус: {current_status}"
            answer = f"Уже обработано: {current_status}"
            alert = True

        case _:
            logger.error(
                "Unexpected moderation outcome: %s",
                result.outcome,
            )
            await query.answer("Неожиданный результат", show_alert=True)
            return

    await query.answer(answer, show_alert=alert)
    await query.edit_message_text(
        f"{message.text}\n\n{verdict}",
    )


async def on_bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает добавление бота в чат.
    """
    chat_member = update.my_chat_member

    if chat_member is None:
        return

    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status

    # Только реальное добавление бота в чат
    if (
        chat_member.chat.type not in ("group", "supergroup")
        or old_status not in ("left", "kicked")
        or new_status not in ("member", "administrator")
    ):
        return

    tg_chat = chat_member.chat

    logger.info(
        "Bot added to chat %s: %s -> %s",
        tg_chat.id,
        old_status,
        new_status,
    )

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        chat_repo = ChatRepository(session)
        chat_service = ChatService(chat_repo)

        chat = await chat_service.register_chat(
            chat_id=tg_chat.id,
            chat_type=tg_chat.type,
            chat_title=tg_chat.title,
            tag_name=tg_chat.username,
        )

    if not chat.is_created:
        logger.debug("Bot has been added back to the chat: %s", tg_chat.id)
        return

    notifier = AdminNotifier(context.bot, settings.admin_ids)
    request_msg = AdminMessages.chat_request(tg_chat)

    await notifier.send(
        text=request_msg,
        reply_markup=approve_chat_keyboard(tg_chat.id),
    )
