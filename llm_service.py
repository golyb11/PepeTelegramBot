# ============================================================================
# llm_service.py — Обёртка над AsyncOpenAI для обращения к OpenRouter
# ============================================================================
# Модуль предоставляет единственную публичную функцию generate_reply(),
# которая:
#   1. Динамически читает актуальные API-ключ и модель из SQLite (через
#      database.get_settings()), чтобы всегда использовать последние
#      значения, заданные командами /setkey и /setmodel.
#   2. Создаёт экземпляр AsyncOpenAI с base_url OpenRouter.
#   3. Отправляет запрос к LLM с двумя сообщениями: system (промпт-персона)
#      и user (текст пользователя).
#   4. Возвращает текстовый ответ модели, либо сообщение об ошибке.
#
# AsyncOpenAI создаётся КАЖДЫЙ раз заново, потому что ключ может измениться
# между запросами. Это осознанный trade-off: незначительный оверхед создания
# клиента vs. гарантия актуальности учётных данных.
# ============================================================================

import logging
from openai import AsyncOpenAI

import database
from config import OPENROUTER_BASE_URL

# Логгер модуля
logger: logging.Logger = logging.getLogger(__name__)


async def generate_reply(system_prompt: str, user_text: str) -> str:
    """
    Сгенерировать ответ LLM через OpenRouter API (без контекста).

    Args:
        system_prompt: Системный промпт, определяющий «личность» бота.
        user_text:     Текст сообщения пользователя.

    Returns:
        str: Текст ответа модели, либо сообщение об ошибке на русском.
    """
    return await generate_reply_with_context(system_prompt, user_text, [])


async def generate_reply_with_context(
    system_prompt: str,
    user_text: str,
    context_messages: list[dict],
) -> str:
    """
    Сгенерировать ответ LLM через OpenRouter API с учетом контекста чата.

    Функция каждый раз заново читает настройки из БД.

    Args:
        system_prompt: Системный промпт, определяющий «личность» бота.
        user_text: Текст сообщения пользователя, на который нужно ответить.
        context_messages: Список словарей с предыдущими сообщениями чата.
                         Каждый словарь должен содержать: username, message_text.

    Returns:
        str: Текст ответа модели, либо сообщение об ошибке на русском.
    """
    try:
        # --- Шаг 1: Получаем актуальные настройки из SQLite ---
        api_key, model_name = await database.get_settings()
        logger.info(
            "LLM-запрос с контекстом: model=%s, context_len=%d, user_text_len=%d",
            model_name, len(context_messages), len(user_text)
        )

        # --- Шаг 2: Создаём клиент AsyncOpenAI ---
        client: AsyncOpenAI = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )

        # --- Шаг 3: Формируем сообщения для модели ---
        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Добавляем контекст (предыдущие сообщения) в обратном порядке
        # (от старых к новым)
        if context_messages:
            context_lines: list[str] = []
            # context_messages приходит уже в порядке от новых к старым,
            # переворачиваем для хронологического порядка
            for msg in reversed(context_messages):
                username = msg.get("username") or f"User{msg.get('user_id', 'Unknown')}"
                text = msg.get("message_text", "")
                context_lines.append(f"{username}: {text}")

            # Добавляем контекст как отдельное системное сообщение
            context_block = "\n".join(context_lines)
            context_prompt = (
                f"Контекст последних сообщений в чате:\n{context_block}\n\n"
                f"Текущее сообщение: {user_text}"
            )
            messages.append({"role": "user", "content": context_prompt})
        else:
            messages.append({"role": "user", "content": user_text})

        # --- Шаг 4: Отправляем запрос к модели ---
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
        )

        # --- Шаг 5: Извлекаем текст ответа ---
        reply_text: str = response.choices[0].message.content or ""
        logger.info("LLM-ответ получен, длина=%d символов.", len(reply_text))
        return reply_text

    except Exception as exc:
        logger.error("Ошибка при обращении к OpenRouter API: %s", exc, exc_info=True)
        return "❌ Ошибка API. Проверьте ключ или модель командами /setkey и /setmodel."
