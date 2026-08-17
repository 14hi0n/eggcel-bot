import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from config import Config
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from keyboards.approve import approve_chat_keyboard

logger = logging.getLogger(__name__)


async def chat_moderate_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info("Админ что-то нажал")
    query = update.callback_query
    _, action, chat_id_str = query.data.split(":")

    logger.info(f"Нажал на {action} в контексте id: {chat_id_str}")

    chat_id = int(chat_id_str)
    status = ChatStatus.approved if action == "approve" else ChatStatus.rejected

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session:
        async with session.begin():
            chat = await ChatRepository(session).set_status(chat_id, status)

    if chat is None:
        await query.answer("Чат не найден в бд", show_alert=True)

    verdict = "Approved" if status == ChatStatus.approved else "Rejected"
    await query.edit_message_text(f"{query.message.text}\n\n{verdict}")
    await query.answer()


async def on_bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.my_chat_member

    if result is None:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # Только реальное добавление бота в чат
    if old_status not in ("left", "kicked") or new_status not in (
        "member",
        "administrator",
    ):
        return

    tg_chat = result.chat

    logger.info(
        "Bot added to chat %s: %s -> %s",
        tg_chat.id,
        old_status,
        new_status,
    )

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session:
        async with session.begin():
            await ChatRepository(session).create_or_reset_pending(
                chat_id=tg_chat.id,
                chat_type=tg_chat.type,
                chat_title=tg_chat.title,
                tag_name=tg_chat.username,
            )

    await notify_admin(
        tg_chat.id,
        tg_chat.title or str(tg_chat.id),
        tg_chat.type,
        tg_chat.username,
        context,
    )


async def on_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        logger.debug("Это не супергруппа и не группа. пропускаю")
        await update.message.reply_text("Эту команду нужно вводить в чате, а не в ЛС")
        return

    tg_chat = update.effective_chat
    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session:
        async with session.begin():
            chat, created = await ChatRepository(session).create_or_reset_pending(
                chat_id=tg_chat.id,
                chat_type=tg_chat.type,
                chat_title=tg_chat.title,
                tag_name=tg_chat.username,
            )

    if created:
        logger.debug("Добавил новый канал и отправил заявку админу")
        await notify_admin(
            tg_chat.id,
            tg_chat.title or str(tg_chat.id),
            tg_chat.type,
            tg_chat.username,
            context,
        )
        await update.message.reply_text("Заявка отправлена")
    else:
        status = chat.status.value
        if status == ChatStatus.pending:
            status = "pegging"
        await update.message.reply_text(f"Текущий статус: {status}")


async def notify_admin(
    chat_id: int,
    chat_title: str,
    chat_type: str,
    chat_tag: str | None,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Sends a notification message to the admin(s) specified in the configuration.

    Args:
        message (str): The message to be sent to the admin(s).
    """
    bot = context.bot
    text = (
        f"Запрос на активацию\n\n"
        f"ID: {chat_id}\n"
        f"Chat Title: {chat_title}\n"
        f"Chat Type: {chat_type}\n"
    )

    if chat_tag is not None:
        text += f"\nChat Tag: {chat_tag}"

    for admin_id in Config.ADMIN_IDS:
        await bot.send_message(
            chat_id=admin_id,
            text=text,
            reply_markup=approve_chat_keyboard(chat_id),
        )
