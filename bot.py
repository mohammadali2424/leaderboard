from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from database import init_db
from handlers.start import start, reg_conv_handler, login_conv_handler
from handlers.menu import menu_handler

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(reg_conv_handler)
    app.add_handler(login_conv_handler)
    app.add_handler(menu_handler)
    # /start command handler (outside conversation)
    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("start", start))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
