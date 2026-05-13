import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatAction
import llm_service
import database
from config import ASSISTANT_SYSTEM_PROMPT

router: Router = Router(name="assistant_router")
logger: logging.Logger = logging.getLogger(__name__)


@router.message(Command("ask"))
async def handle_ask(message: Message) -> None:

    raw_text: str = message.text or ""
    parts: list[str] = raw_text.split(maxsplit=1)


    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        message_text=raw_text,
    )

    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "❓ Задай вопрос после команды.\n"
            "Пример: `/ask Какая самая глубокая точка океана?`",
            parse_mode="Markdown",
        )
        return

    question: str = parts[1].strip()
    logger.info("Получен /ask от user_id=%d: '%s'", message.from_user.id, question[:80])


    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)


    reply_text: str = await llm_service.generate_reply(
        system_prompt=ASSISTANT_SYSTEM_PROMPT, user_text=question,
    )

    await message.reply(reply_text)
    logger.info("Ответ на /ask отправлен user_id=%d.", message.from_user.id)
