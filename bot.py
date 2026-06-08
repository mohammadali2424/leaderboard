import logging
import sqlite3
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
TOKEN = "YOUR_BOT_TOKEN" # توکن بات
ADMIN_ID = 123456789 # ایدی عددی ادمین
GROUP_ID = -1001234567890 # ایدی گروه برای لیدربورد

# ======================== دیتابیس ========================
conn = sqlite3.connect("points.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)"
)
conn.commit()


def get_points(user_id: int) -> int:
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0


def add_points(user_id: int, delta: int) -> int:
    current = get_points(user_id)
    new_points = current + delta
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, points) VALUES (?, ?)",
        (user_id, new_points),
    )
    conn.commit()
    return new_points


def top_users(limit: int = 10):
    cursor.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
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

    # اطلاع‌رسانی به کاربر
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"🎉 تبریک!\nادمین <b>{amount}</b> امتیاز به شما اضافه کرد.\n"
                 f"موجودی فعلی: <b>{new_pts}</b> ⭐",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ <b>{amount}</b> امتیاز به کاربر <code>{uid}</code> اضافه شد.\n"
        f"موجودی جدید: <b>{new_pts}</b> ⭐",
        parse_mode="HTML",
    )
    return await back_to_menu(update, context)


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
            text=f"⚠️ توجه!\nادمین <b>{amount}</b> امتیاز از شما کم کرد.\n"
                 f"موجودی فعلی: <b>{new_pts}</b> ⭐",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ <b>{amount}</b> امتیاز از کاربر <code>{uid}</code> کم شد.\n"
        f"موجودی جدید: <b>{new_pts}</b> ⭐",
        parse_mode="HTML",
    )
    return await back_to_menu(update, context)


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
    try:
        chat = await context.bot.get_chat(uid)
        name = chat.first_name or "کاربر"
    except Exception:
        name = "ناشناس"

    await update.message.reply_text(
        f"👤 <b>اطلاعات کاربر</b>\n"
        f"آیدی: <code>{uid}</code>\n"
        f"نام: {name}\n"
        f"امتیاز: <b>{pts}</b> ⭐",
        parse_mode="HTML",
    )
    return await back_to_menu(update, context)


# ======================== بازگشت به منو ========================
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ افزودن امتیاز", "➖ کاهش امتیاز"],
        ["📊 اطلاعات کاربر"],
        ["❌ خروج"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🔙 به منوی اصلی برگشتید. چه کاری انجام دهم؟", reply_markup=markup)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ افزودن امتیاز", "➖ کاهش امتیاز"],
        ["📊 اطلاعات کاربر"],
        ["❌ خروج"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=markup)
    return ConversationHandler.END


async def exit_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 خداحافظ! برای ورود دوباره /start را بزنید.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ======================== لیدربورد (فقط گروه) ========================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        await update.message.reply_text("⛔ این دستور فقط در گروه مخصوص قابل استفاده است.")
        return

    top = top_users(10)
    if not top:
        await update.message.reply_text("🏆 هنوز هیچ امتیازی ثبت نشده.")
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>لیدربورد امتیازات</b> 🏆\n\n"
    for i, (uid, pts) in enumerate(top):
        try:
            chat = await context.bot.get_chat(uid)
            name = chat.first_name or "کاربر"
        except Exception:
            name = "ناشناس"
        rank = i + 1
        medal = medals[i] if i < 3 else "⭐"
        text += f"{medal} <b>{rank}</b>. {name} (<code>{uid}</code>) → {pts} امتیاز\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ======================== اجرای ربات ========================
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()

    # هندلر مکالمه (پنل ادمین)
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^(➕ افزودن امتیاز)$") & filters.ChatType.PRIVATE & filters.User(ADMIN_ID),
                add_start,
            ),
            MessageHandler(
                filters.Regex("^(➖ کاهش امتیاز)$") & filters.ChatType.PRIVATE & filters.User(ADMIN_ID),
                rem_start,
            ),
            MessageHandler(
                filters.Regex("^(📊 اطلاعات کاربر)$") & filters.ChatType.PRIVATE & filters.User(ADMIN_ID),
                info_start,
            ),
            MessageHandler(
                filters.Regex("^(❌ خروج)$") & filters.ChatType.PRIVATE & filters.User(ADMIN_ID),
                exit_panel,
            ),
        ],
        states={
            ADD_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_uid)],
            ADD_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amt)],
            REM_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, rem_uid)],
            REM_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, rem_amt)],
            INFO_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_uid)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^(خروج)$"), cancel),
        ],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    # پیام برای دستورات ناشناس
    async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⚠️ دستور نامعتبر است.")

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("✅ ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
