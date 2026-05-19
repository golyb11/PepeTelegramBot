# ============================================================================
# llm_router.py — Запросы к OpenRouter API (через openai SDK)
# ============================================================================

import logging
from openai import AsyncOpenAI
from config import OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)


async def ask_llm(
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
) -> str:
    """
    Отправляет запрос к OpenRouter и возвращает текст ответа.

    :param api_key: API-ключ OpenRouter
    :param model: Идентификатор модели
    :param system_prompt: Системный промпт
    :param messages: Список сообщений [{"role": "user"/"assistant", "content": "..."}]
    :param max_tokens: Макс. длина ответа
    :return: Текст ответа или сообщение об ошибке
    """
    client = AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/golyb11/PepeTelegramBot",
            "X-Title": "Pepe Telegram Bot"
        }
    )

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return choice.message.content or "🤷 Модель вернула пустой ответ."

    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            return "❌ API-ключ невалидный или истёк. Используй /setkey для замены."
        if "429" in error_str or "rate" in error_str:
            return "❌ Слишком много запросов. Подожди немного и попробуй снова."
        if "timeout" in error_str:
            return "❌ OpenRouter не отвечает (таймаут). Попробуй позже."
        logger.error("LLM error: %s", e)
        return "❌ OpenRouter завис или отвалился ключ. Проверь баланс или подожди."
