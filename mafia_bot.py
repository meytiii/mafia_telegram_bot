from telegram import Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = 'YOUR_TOKEN'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = "به بات بازی مافیا خوش آمدید! لطفاً یک گزینه را از منو انتخاب کنید."
    keyboard = [
        [
            InlineKeyboardButton("ایجاد بازی مافیا", callback_data='create_game'),
            InlineKeyboardButton("مشاهده قوانین", callback_data='view_rules')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rules_text = (
        "قوانین بازی مافیا:\n"
        "1. دو تیم اصلی وجود دارد: مافیا و شهروندان.\n"
        "2. بازی دو فاز دارد: روز و شب.\n"
        "3. در شب، مافیا به طور مخفیانه یک شهروند را انتخاب می‌کند تا حذف کند.\n"
        "4. در روز، همه بازیکنان بحث می‌کنند و رای می‌دهند تا یک مظنون را حذف کنند.\n"
        "5. بازی ادامه می‌یابد تا زمانی که یا مافیا حذف شود یا مافیا بیشتر از شهروندان شود.\n"
        "6. نقش‌ها و قوانین اضافی می‌توانند برای افزایش جذابیت بازی اضافه شوند."
    )
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=rules_text)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'create_game':
        await query.edit_message_text(text="در حال ایجاد بازی مافیا... (ویژگی هنوز پیاده‌سازی نشده است)")
    elif query.data == 'view_rules':
        await rules(update, context)

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
