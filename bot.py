import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from supabase import create_client

# ======================== تنظیمات اولیه ========================
TOKEN = os.getenv("YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

# ======================== اتصال به Supabase ========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================== دیتابیس ========================
def get_points(user_id: int) -> int:
    result = supabase.table("users").select("points").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]["points"]
    return 0

def add_points(user_id: int, delta: int) -> int:
    current = get_points(user_id)
    new_points = current + delta
    supabase.table("users").upsert({"user_id": user_id, "points": new_points}).execute()
    return new_points

def top_users(limit: int = 10):
    result = supabase.table("users").select("*").order("points", desc=True).limit(limit).execute()
    return [(row["user_id"], row["points"]) for row in result.data]

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
    text = "🏆 <b>لیدربورد امتیازات</b
