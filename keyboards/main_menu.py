from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚽ بازی‌های امروز", callback_data="matches")],
        [InlineKeyboardButton("📊 جدول گروه‌ها", callback_data="table")],
        [InlineKeyboardButton("🎯 پیش‌بینی بازی", callback_data="predict")],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard")],
        [InlineKeyboardButton("👤 پروفایل من", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)
