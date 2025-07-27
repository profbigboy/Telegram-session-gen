from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN
from session_worker import send_code, verify_code
import asyncio

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("📱 Single Session String", callback_data="single_session")],
        [InlineKeyboardButton("📦 Bulk Session String", callback_data="bulk_session")],
    ]
    await update.message.reply_text(
        "Welcome! Choose an option:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "single_session":
        user_data[user_id] = {"mode": "single", "step": "ask_phone"}
        await query.message.reply_text("📞 Enter your phone number (with country code):")

    elif query.data == "bulk_session":
        user_data[user_id] = {
            "mode": "bulk",
            "step": "ask_bulk_numbers",
            "numbers": [],
            "sessions": [],
        }
        await query.message.reply_text(
            "📋 Enter phone numbers vertically (one per line, with country code):"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        return await update.message.reply_text("❗ Please click /start first.")

    data = user_data[user_id]
    mode = data.get("mode")
    step = data.get("step")

    if mode == "single":
        if step == "ask_phone":
            phone = update.message.text.strip()
            data["phone"] = phone
            data["step"] = "ask_otp"
            await update.message.reply_text(f"📨 Sending OTP to {phone}...")
            await send_code(phone)
            await update.message.reply_text("✅ OTP sent. Please enter the OTP you received:")

        elif step == "ask_otp":
            otp = update.message.text.strip()
            phone = data["phone"]
            await update.message.reply_text("🧠 Verifying...")

            session_str = await verify_code(phone, otp)

            if "session" in session_str or "1A" in session_str:
                await update.message.reply_text(f"✅ Session generated:\n`{session_str}`", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Failed: {session_str}")

            user_data.pop(user_id, None)

    elif mode == "bulk":
        if step == "ask_bulk_numbers":
            numbers = update.message.text.strip().splitlines()
            data["numbers"] = numbers
            data["step"] = "ask_bulk_otp"
            data["current_index"] = 0

            first_number = numbers[0]
            data["current_phone"] = first_number
            await update.message.reply_text(f"📨 Sending OTP to {first_number}...")
            await send_code(first_number)
            await update.message.reply_text(f"✅ OTP sent to {first_number}. Please enter the OTP:")

        elif step == "ask_bulk_otp":
            otp = update.message.text.strip()
            phone = data["current_phone"]

            await update.message.reply_text("🧠 Verifying...")

            session_str = await verify_code(phone, otp)
            if "session" in session_str or "1A" in session_str:
                await update.message.reply_text(f"✅ Session for {phone}:\n`{session_str}`", parse_mode='Markdown')
                data["sessions"].append((phone, "✅ Success"))
            else:
                await update.message.reply_text(f"❌ Failed for {phone}: {session_str}")
                data["sessions"].append((phone, "❌ Failed"))

            # Move to next number
            data["current_index"] += 1
            if data["current_index"] < len(data["numbers"]):
                next_number = data["numbers"][data["current_index"]]
                data["current_phone"] = next_number
                await update.message.reply_text(f"📨 Sending OTP to {next_number}...")
                await send_code(next_number)
                await update.message.reply_text(f"✅ OTP sent to {next_number}. Please enter the OTP:")
            else:
                summary = "\n".join([f"{phone}: {status}" for phone, status in data["sessions"]])
                await update.message.reply_text("✅ All done! Summary:\n\n" + summary)
                user_data.pop(user_id, None)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
