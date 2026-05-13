


















import logging
import re

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatAction

import llm_service
import database
from config import PEPE_SYSTEM_PROMPT, COMMENT_SYSTEM_PROMPT


router: Router = Router(name="pepe_router")


logger: logging.Logger = logging.getLogger(__name__)


COMMENT_TRIGGERS: list[str] = [
    r"че\s+скаж[еэ]шь\s+п[эе]п[аэ]",
    r"че\s+дума[еэ]шь",
    r"на\s+твой\s+вкус",
]


def is_comment_trigger(text: str) -> bool:

    text_lower = text.lower()
    for pattern in COMMENT_TRIGGERS:
        if re.search(pattern, text_lower):
            return True
    return False


def contains_pepe(text: str) -> bool:

    text_lower = text.lower()

    if is_comment_trigger(text):
        return False
    return "пэпэ" in text_lower


def is_not_command(text: str | None) -> bool:

    if not text:
        return False
    return not text.startswith("/")


@router.message(F.text, lambda msg: is_not_command(msg.text))
async def save_and_handle_message(message: Message) -> None:







    if not message.text:
        return


    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        message_text=message.text,
    )

    text = message.text


    if is_comment_trigger(text):
        await handle_comment_trigger(message)
        return


    if contains_pepe(text):
        await handle_pepe_mention(message)


async def handle_comment_trigger(message: Message) -> None:





    logger.info(
        "Триггер комментирования от user_id=%d в chat_id=%d: '%s'",
        message.from_user.id,
        message.chat.id,
        message.text[:80],
    )


    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )


    context = await database.get_chat_history(message.chat.id, limit=10)


    reply_text: str = await llm_service.generate_reply_with_context(
        system_prompt=COMMENT_SYSTEM_PROMPT,
        user_text=message.text,
        context_messages=context,
    )


    await message.reply(reply_text)
    logger.info("Комментарий Пэпэ отправлен в chat_id=%d.", message.chat.id)


async def handle_pepe_mention(message: Message) -> None:






    logger.info(
        "Триггер 'Пэпэ' от user_id=%d в chat_id=%d: '%s'",
        message.from_user.id,
        message.chat.id,
        message.text[:80],
    )


    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )


    context = await database.get_chat_history(message.chat.id, limit=5)


    reply_text: str = await llm_service.generate_reply_with_context(
        system_prompt=PEPE_SYSTEM_PROMPT,
        user_text=message.text,
        context_messages=context,
    )


    await message.reply(reply_text)
    logger.info("Ответ Пэпэ отправлен в chat_id=%d.", message.chat.id)
