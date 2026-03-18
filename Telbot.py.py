from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "8764674676:AAHg99oU31y5Gp7ffbJCDjFg32WyUMCmq6o"

ADMINS = [6290649689]  # admin ID
GROUP_ID = -1003824264170  # group ID

pending = {}

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Approve", callback_data=f"approve_{msg.message_id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject_{msg.message_id}")
        ]
    ])

    for admin in ADMINS:
        if msg.photo:
            await context.bot.send_photo(
                chat_id=admin,
                photo=msg.photo[-1].file_id,
                caption="New report",
                reply_markup=keyboard
            )
        else:
            text = msg.text if msg.text else "New report"
            await context.bot.send_message(
                chat_id=admin,
                text=text,
                reply_markup=keyboard
            )

    pending[msg.message_id] = msg


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, msg_id = query.data.split("_")
    msg_id = int(msg_id)

    if msg_id not in pending:
        await query.edit_message_text("Done")
        return

    original_msg = pending[msg_id]

    if action == "approve":
        if original_msg.text:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=original_msg.text,
                message_thread_id=original_msg.message_thread_id
            )
        elif original_msg.photo:
            await context.bot.send_photo(
                chat_id=GROUP_ID,
                photo=original_msg.photo[-1].file_id,
                message_thread_id=original_msg.message_thread_id
            )

        await query.edit_message_text("Approved")

    elif action == "reject":
        await query.edit_message_text("Rejected")

    del pending[msg_id]


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.ALL, handle))
app.add_handler(CallbackQueryHandler(button))

print("Bot started...")
app.run_polling()