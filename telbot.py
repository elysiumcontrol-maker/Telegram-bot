import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ===== CONFIG =====
TOKEN =  "8764674676:AAHHMHHek4l_-YZnzWaQAOHtjGD172ptX8o"
GROUP_ID = -1003824264170
ADMINS = [6290649689]

pending = {}

# ===== RENDER SERVER (port нээх) =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# ===== MESSAGE HANDLE =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    msg_id = msg.message_id
    pending[msg_id] = msg

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{msg_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{msg_id}")
        ]
    ])

    for admin in ADMINS:
        if msg.text:
            await context.bot.send_message(
                chat_id=admin,
                text=f"Шинэ тайлан:\n\n{msg.text}",
                reply_markup=keyboard
            )
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=admin,
                photo=msg.photo[-1].file_id,
                caption="Шинэ фото тайлан",
                reply_markup=keyboard
            )

# ===== BUTTON HANDLE =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, msg_id = query.data.split("_")
    msg_id = int(msg_id)

    user_id = query.from_user.id
    if user_id not in ADMINS:
        await query.answer("Permission denied", show_alert=True)
        return

    if msg_id not in pending:
        await query.edit_message_text("Already handled")
        return

    original_msg = pending[msg_id]

    if action == "approve":
        if original_msg.text:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=original_msg.text
            )
        elif original_msg.photo:
            await context.bot.send_photo(
                chat_id=GROUP_ID,
                photo=original_msg.photo[-1].file_id
            )

        await query.edit_message_text("✅ Approved")

    elif action == "reject":
        await query.edit_message_text("❌ Rejected")

    del pending[msg_id]

# ===== MAIN =====
def main():
    threading.Thread(target=run_server).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle))
    app.add_handler(CallbackQueryHandler(button))

    print("BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
