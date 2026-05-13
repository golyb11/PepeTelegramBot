

















import logging
from openai import AsyncOpenAI

import database
from config import OPENROUTER_BASE_URL


logger: logging.Logger = logging.getLogger(__name__)


async def generate_reply(system_prompt: str, user_text: str) -> str:










    return await generate_reply_with_context(system_prompt, user_text, [])


async def generate_reply_with_context(
    system_prompt: str,
    user_text: str,
    context_messages: list[dict],
) -> str:














    try:

        api_key, model_name = await database.get_settings()
        logger.info(
            "LLM-запрос с контекстом: model=%s, context_len=%d, user_text_len=%d",
            model_name, len(context_messages), len(user_text)
        )


        client: AsyncOpenAI = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )


        messages: list[dict] = [{"role": "system", "content": system_prompt}]



        if context_messages:
            context_lines: list[str] = []


            for msg in reversed(context_messages):
                username = msg.get("username") or f"User{msg.get('user_id', 'Unknown')}"
                text = msg.get("message_text", "")
                context_lines.append(f"{username}: {text}")


            context_block = "\n".join(context_lines)
            context_prompt = (
                f"Контекст последних сообщений в чате:\n{context_block}\n\n"
                f"Текущее сообщение: {user_text}"
            )
            messages.append({"role": "user", "content": context_prompt})
        else:
            messages.append({"role": "user", "content": user_text})


        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
        )


        reply_text: str = response.choices[0].message.content or ""
        logger.info("LLM-ответ получен, длина=%d символов.", len(reply_text))
        return reply_text

    except Exception as exc:
        logger.error("Ошибка при обращении к OpenRouter API: %s", exc, exc_info=True)
        return "❌ Ошибка API. Проверьте ключ или модель командами /setkey и /setmodel."
