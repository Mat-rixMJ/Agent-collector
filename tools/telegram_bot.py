"""Telegram gateway. Two jobs:
1. push_summary() — send the kanban snapshot after every orchestration loop.
2. run_listener() — long-poll for incoming messages so a human can chat with
   the agent team ("what's the status of the ads pipeline?") — routes the text
   straight to the LLM with kanban + latest outputs as context.
"""
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from tools import kanban
from tools.llm_client import ask

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def push_summary(text: str | None = None) -> None:
    if not TOKEN or not CHAT_ID:
        print("[telegram_bot] TELEGRAM_BOT_TOKEN/CHAT_ID not set — skipping push.")
        return
    import asyncio

    async def _send():
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text or kanban.snapshot(), parse_mode="Markdown")

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"[telegram_bot] Failed to send: {e}")


async def _on_message(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    board = kanban.snapshot()
    reply = ask(
        system_prompt=(
            "You are the CrowdWisdomTrading marketing agent team's status assistant. "
            "Answer questions about current progress using the kanban board context given. "
            "Be concise."
        ),
        user_prompt=f"Kanban board:\n{board}\n\nQuestion: {user_text}",
    )
    await update.message.reply_text(reply)


def run_listener() -> None:
    """Blocking call — run this in its own process to let the team chat over Telegram."""
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))
    app.run_polling()


if __name__ == "__main__":
    run_listener()
