from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import database as db

# State‌های ثبت‌نام و ورود
REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_CONFIRM = range(3)
LOGIN_USERNAME, LOGIN_PASSWORD = range(3, 5)

# منوی اصلی (ایمپورت می‌کنیم)
from keyboards.main_menu import main_menu_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if db.user_exists(chat_id):
        username = db.get_username(chat_id)
        await update.message.reply_text(
            f"خوش برگشتی {username} جان! ⚽",
            reply_markup=main_menu_keyboard()
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام", callback_data="register")],
            [InlineKeyboardButton("🔑 ورود", callback_data="login")],
        ]
        await update.message.reply_text(
            "به اکلیس اسپورت خوش اومدی! 🏆\n"
            "برای شروع یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------- ثبت‌نام ----------
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👤 یک نام کاربری انتخاب کن (فقط حروف و عدد):")
    return REGISTER_USERNAME

async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    if not username.isalnum():
        await update.message.reply_text("❌ فقط حروف و عدد مجاز. دوباره بنویس:")
        return REGISTER_USERNAME
    context.user_data["reg_username"] = username
    await update.message.reply_text("🔒 رمز عبور خودت رو وارد کن (حداقل ۴ کاراکتر):")
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("❌ رمز عبور باید حداقل ۴ کاراکتر باشه. دوباره بفرست:")
        return REGISTER_PASSWORD
    context.user_data["reg_password"] = password
    await update.message.reply_text("🔁 رمز عبور رو یک بار دیگه وارد کن:")
    return REGISTER_CONFIRM

async def register_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() != context.user_data["reg_password"]:
        await update.message.reply_text("❌ رمزها یکسان نیستند. دوباره رمز عبور رو وارد کن:")
        return REGISTER_PASSWORD
    chat_id = update.effective_chat.id
    success = db.register_user(
        chat_id,
        context.user_data["reg_username"],
        context.user_data["reg_password"]
    )
    if success:
        await update.message.reply_text(
            f"✅ ثبت‌نام موفق! خوش اومدی {context.user_data['reg_username']} جان.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ این نام کاربری قبلاً ثبت شده یا خطایی رخ داده. /start رو بزن دوباره."
        )
    return ConversationHandler.END

# ---------- ورود ----------
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👤 نام کاربری‌ات رو وارد کن:")
    return LOGIN_USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_username"] = update.message.text.strip()
    await update.message.reply_text("🔒 رمز عبور رو وارد کن:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = context.user_data["login_username"]
    password = update.message.text.strip()
    if db.login_user(chat_id, username, password):
        await update.message.reply_text(
            f"🎉 ورود موفق! خوش اومدی {username} جان.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text("❌ نام کاربری یا رمز عبور اشتباه. /start رو بزن دوباره.")
    return ConversationHandler.END

# کنسل کردن
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد. /start رو بزن.")
    return ConversationHandler.END

# تعریف هندلرهای ثبت‌نام و ورود به صورت ConversationHandler
reg_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(register_start, pattern="^register$")],
    states={
        REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
        REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        REGISTER_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

login_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(login_start, pattern="^login$")],
    states={
        LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
        LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
