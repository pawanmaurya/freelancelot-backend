import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import logging

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Your Telegram bot token
BACKEND_LINK_ENDPOINT = os.getenv("BACKEND_LINK_ENDPOINT")  # e.g., http://localhost:8000/api/link-telegram

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Received /start command from chat_id={chat_id}, args={context.args}")
    if context.args:
        user_token = context.args[0]
        try:
            resp = requests.post(
                BACKEND_LINK_ENDPOINT,
                json={"user_token": user_token, "chat_id": chat_id}
            )
            logger.info(f"POST to BACKEND_LINK_ENDPOINT with user_token={user_token}, chat_id={chat_id}, status_code={resp.status_code}")
            if resp.status_code == 200:
                await update.message.reply_text("✅ Your Telegram is now linked! Please create job filters on <a href='https://freelancelot.app/dashboard'>dashboard</a> to start recieving job alerts.")
                logger.info(f"Sent success message to chat_id={chat_id}")
            elif resp.status_code == 404:
                await update.message.reply_text("⚠️ User not found. Please signup first on <a href='https://freelancelot.app'>Freelancelot</a>.", parse_mode="HTML")
                logger.info(f"Sent user not found message to chat_id={chat_id}")
            else:
                await update.message.reply_text("⚠️ Failed to link Telegram. Please try again or contact support.")
                logger.info(f"Sent generic failure message to chat_id={chat_id}")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")
            logger.error(f"Exception during linking for chat_id={chat_id}: {e}")
    else:
        welcome_message = (
            "👋 Welcome to Freelancelot Alert Bot!\n\n"
            "Get instant Upwork job alerts from Freelancelot.app right here on Telegram.\n\n"
            "To link your account, please copy the /start command from your dashboard: https://freelancelot.app/profile\n\n"
            "If you need help, visit our website or contact support."
        )
        await update.message.reply_text(welcome_message)
        logger.info(f"Sent welcome message to chat_id={chat_id}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()

if __name__ == "__main__":
    main() 