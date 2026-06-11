from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
import database as db

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id

    if data == "matches":
        text = "⚽ بازی‌های امروز هنوز شروع نشده. منتظر جام جهانی باش!"
    elif data == "table":
        text = "📊 جدول گروه‌ها بعد از شروع بازی‌ها فعال میشه."
    elif data == "predict":
        text = "🎯 پیش‌بینی بازی‌ها به زودی..."
    elif data == "leaderboard":
        text = "🏆 لیدربورد هنوز خالیه. اولین نفری که پیش‌بینی کنه!"
    elif data == "profile":
        username = db.get_username(chat_id)
        if username:
            text = f"👤 نام کاربری: {username}\n🏆 امتیاز: هنوز فعال نشده"
        else:
            text = "❌ پروفایل پیدا نشد. /start رو بزن."
    elif data == "help":
        text = (
            "ℹ️ راهنما:\n"
            "⚽ بازی‌های امروز: نمایش برنامه بازی‌ها\n"
            "📊 جدول: جدول گروه‌ها\n"
            "🎯 پیش‌بینی: ثبت پیش‌بینی\n"
            "🏆 لیدربورد: امتیازات کاربران\n"
            "👤 پروفایل: اطلاعات حساب شما"
        )
    else:
        text = "متوجه نشدم."

    await query.edit_message_text(text)

menu_handler = CallbackQueryHandler(menu_callback, pattern="^(matches|table|predict|leaderboard|profile|help)$")
