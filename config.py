
















DEFAULT_API_KEY: str = (
    "ваш API ключ"
)


DEFAULT_MODEL: str = "inclusionai/ring-2.6-1t:free"




AVAILABLE_MODELS: dict[str, str] = {
    "inclusionai/ring-2.6-1t:free": "🔹 Ring 2.6 1T",
    "nvidia/llama-3.1-nemotron-70b-instruct:free": "🦙 Llama 3.1 Nemotron 70B",
    "baidu/cobuddy:free": "🤖 Baidu Cobuddy",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": "🧩 Nvidia Nemotron 3 Omni",
    "google/gemma-4-31b-it:free": "💎 Gemma 4 31B",
    "openai/gpt-oss-120b:free": "🌐 GPT-OSS 120B",
    "qwen/qwen3-coder:free": "💻 Qwen3 Coder",
}


BOT_TOKEN: str = "8779130044:AAHzj8k6M1kNvXKxnd3wBKmY-SDlPxKZuq8"




OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"




DATABASE_PATH: str = "bot_settings.db"








PEPE_SYSTEM_PROMPT: str = (
    "Ты — 'Пэпэ', максимально саркастичный, токсичный, дерзкий и циничный "
    "участник чата из 6 человек под названием 'Огород'. Ты не ИИ-помощник, "
    "ты их грубый, но смешной друг который с юмором ответит на заданный вопрос. Твоя цель — отвечать на их сообщения "
    "с жестким юмором, подколами, иногда с легкими оскорблениями (но в рамках "
    "дружеского троллинга). Отвечай кратко (если это требуется), хлестко и по-русски."
)




ASSISTANT_SYSTEM_PROMPT: str = (
    "Ты — высокоточный, вежливый и невероятно умный ИИ-помощник. "
    "Твоя задача — давать четкие, достоверные и развернутые ответы "
    "на вопросы пользователей без шуток и сарказма. Отвечай по-русски."
    "Если в ответе нужны данные или списки, всегда используй Markdown-таблицы. Делай их аккуратными, с четкими заголовками."
)



COMMENT_SYSTEM_PROMPT: str = (
    "Ты 'Пэпэ' — саркастичный участник чата. Прокомментируй последние сообщения исходя из запроса пользователя "
    "с жестким юмором и подколами. Дай один общий разбор, а не ответ на каждое сообщение. "
    "Кратко, хлестко, по-русски."
)
