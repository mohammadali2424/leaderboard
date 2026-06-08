import logging
import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ======================== تنظیمات اولیه ========================
TOKEN = os.getenv("BOT_TOKEN")  # توکن بات را از ENV بگیر
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # ادمین
GROUP_ID = int(os.getenv("GROUP_ID", "-1001234567890"))  # گروه لیدربورد

# ======================== دیتابیس ========================
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, points INT DEFAULT 0)"
)
conn.commit()


def get_points(user_id: int) -> int:
    cursor.execute("SELECT points FROM users WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0


def add_points(user_id: int, delta: int) -> int:
    current = get_points(user_id)
    new_points = current + delta
    cursor.execute(
        "INSERT INTO users (user_id, points) VALUES (%s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET points = EXCLUDED.points",
        (user_id, new_points),
    )
    conn.commit()
    return new_points


def top_users(limit: int = 10):
    cursor.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT %s", (limit,))
    return cursor.fetchall()


# ======================== وضعیت‌های مکالمه ========================
ADD_UID, ADD_AMT, REM_UID, REM_AMT, INFO_UID = range(5)


# ======================== منوی اصلی ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        keyboard = [
            ["➕ افزودن امتیاز", "➖ کاهش امتیاز"],
            ["📊 اطلاعات کاربر"],
            ["❌ خروج"],
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"🎉 سلام ادمین عزیز {user.first_name}!\n"
            "به پنل مدیریت امتیازات خوش آمدید.\n"
            "از دکمه‌های زیر استفاده کنید.",
            reply_markup=markup,
        )
    else:
        await update.message.reply_text(
            "👋 سلام!\n"
            "این ربات مخصوص مدیریت امتیازات است و شما دسترسی ادمین ندارید.\n"
            "برای دیدن لیدربورد در گروه مخصوص از /leaderboard استفاده کنید."
        )


# ======================== افزودن امتیاز ========================
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔢 آیدی عددی کاربر را وارد کنید:", reply_markup=ReplyKeyboardRemove())
    return ADD_UID


async def add_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")
        return ADD_UID
    context.user_data["target_id"] = int(text)
    await update.message.reply_text("➕ مقدار امتیاز برای افزودن:")
    return ADD_AMT


async def add_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.lstrip("-").isdigit():
        await update.message.reply_text("❌ یک عدد صحیح وارد کنید.")
        return ADD_AMT
    amount = int(text)
    uid = context.user_data["target_id"]
    new_pts = add_points(uid, amount)

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"🎉 تبریک! {amount} امتیاز به شما اضافه شد.\nموجودی فعلی: {new_pts} ⭐",
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ {amount} امتیاز به کاربر {uid} اضافه شد.\nموجودی جدید: {new_pts} ⭐"
    )
    return ConversationHandler.END


# ======================== کاهش امتیاز ========================
async def rem_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔢 آیدی عددی کاربر را وارد کنید:", reply_markup=ReplyKeyboardRemove())
    return REM_UID


async def rem_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ عدد معتبر وارد کنید.")
        return REM_UID
    context.user_data["target_id"] = int(text)
    await update.message.reply_text("➖ مقدار امتیاز برای کاهش:")
    return REM_AMT


async def rem_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.lstrip("-").isdigit():
        await update.message.reply_text("❌ یک عدد صحیح وارد کنید.")
        return REM_AMT
    amount = int(text)
    uid = context.user_data["target_id"]
    new_pts = add_points(uid, -amount)

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"⚠️ {amount} امتیاز از شما کم شد.\nموجودی فعلی: {new_pts} ⭐",
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ {amount} امتیاز از کاربر {uid} کم شد.\nموجودی جدید: {new_pts} ⭐"
    )
    return ConversationHandler.END


# ======================== اطلاعات کاربر ========================
async def info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔢 آیدی عددی کاربر را وارد کنید:", reply_markup=ReplyKeyboardRemove())
    return INFO_UID


async def info_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ عدد معتبر وارد کنید.")
        return INFO_UID
    uid = int(text)
    pts = get_points(uid)
    await update.message.reply_text(
        f"👤 اطلاعات کاربر\nآیدی: {uid}\nامتیاز: {pts} ⭐"
    )
    return ConversationHandler.END


# ======================== لیدربورد ========================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        await update.message.reply_text("⛔ این دستور فقط در گروه مخصوص قابل استفاده است.")
        return

    top = top_users(10)
    if not top:
        await update.message.reply_text("🏆 هنوز هیچ امتیازی ثبت نشده.")
        return

    text = "🏆 لیدربورد امتیازات 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, pts) in enumerate(top):
        rank = i + 1
        medal = medals[i] if i < 3 else "⭐"
        text += f"{medal} {rank}. {uid} → {pts} امتیاز\n"

    await update.message.reply_text(text)


# ======================== اجرای ربات ========================
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(➕ افزودن امتیاز)$") & filters.User(ADMIN_ID), add_start),
            MessageHandler(filters.Regex("^(➖ کاهش امتیاز)$") & filters.User(ADMIN_ID), rem_start),
            MessageHandler(filters.Regex("^(📊 اطلاعات کاربر)$") & filters.User(ADMIN_ID), info_start),
        ],
        states={
            ADD_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_uid)],
            ADD_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amt)],
            REM_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, rem_uid)],
            REM_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, rem_amt)],
            INFO_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_uid)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.run_polling()


if __name__ == "__main__":
    main()
