from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio

TOKEN = "8764674676:AAHHMHHek4l_-YZnzWaQAOHtjGD172ptX8o"
ADMINS = [2132894043, 6290649689]


pending = {}
albums = {}

async def send_album_preview(context, mgid):
    await asyncio.sleep(0.8)

    if mgid not in albums:
        return

    album = albums[mgid]

    media = []
    for m in album["messages"]:
        media.append(InputMediaPhoto(media=m.photo[-1].file_id))

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"album_{mgid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_album_{mgid}")
    ]]

    for admin in ADMINS:
        sent_msgs = await context.bot.send_media_group(
            chat_id=admin,
            media=media
        )

        for m in sent_msgs:
            album["admin_media"].append((admin, m.message_id))

        first = album["messages"][0]
        caption = first.caption or f"📷 Album ({len(media)} зураг)"

        sent = await context.bot.send_message(
            chat_id=admin,
            text=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        album["admin_msgs"].append((admin, sent.message_id))


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type not in ["group", "supergroup"]:
        return

    try:
        await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
    except:
        pass

    if msg.media_group_id:
        mgid = msg.media_group_id

        if mgid not in albums:
            albums[mgid] = {
                "messages": [],
                "chat_id": msg.chat_id,
                "thread_id": msg.message_thread_id,
                "user": msg.from_user,
                "admin_msgs": [],
                "admin_media": [],
                "task": None
            }

        albums[mgid]["messages"].append(msg)

        if albums[mgid]["task"]:
            albums[mgid]["task"].cancel()

        albums[mgid]["task"] = asyncio.create_task(send_album_preview(context, mgid))

    elif msg.photo:
        key = f"{msg.chat_id}_{msg.message_id}"

        pending[key] = {
            "msg": msg,
            "thread_id": msg.message_thread_id,
            "admin_msgs": []
        }

        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{key}")
        ]]

        for admin in ADMINS:
            sent = await context.bot.send_photo(
                chat_id=admin,
                photo=msg.photo[-1].file_id,
                caption=msg.caption or "📷 Photo",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            pending[key]["admin_msgs"].append((admin, sent.message_id))

    elif msg.text:
        key = f"{msg.chat_id}_{msg.message_id}"

        pending[key] = {
            "msg": msg,
            "thread_id": msg.message_thread_id,
            "admin_msgs": []
        }

        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{key}")
        ]]

        for admin in ADMINS:
            sent = await context.bot.send_message(
                chat_id=admin,
                text=msg.text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            pending[key]["admin_msgs"].append((admin, sent.message_id))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("approve_"):
        key = data.replace("approve_", "")

        if key not in pending:
            await query.edit_message_text("⛔ Already processed")
            return

        item = pending[key]
        msg = item["msg"]
        thread_id = item["thread_id"]
        for admin_id, message_id in item["admin_msgs"]:
            try:
                await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
            except:
                pass

        user = msg.from_user
        approver = query.from_user

        name = user.full_name
        username = f"@{user.username}" if user.username else "username байхгүй"
        approver_name = approver.full_name

        if msg.text:
            text = f"{msg.text}\n\n👤 {name}\n📞 {username}\n\n✅ Approved by {approver_name}"

            await context.bot.send_message(
                chat_id=msg.chat_id,
                text=text,
                message_thread_id=thread_id
            )

        elif msg.photo:
            caption = msg.caption or ""
            text = f"{caption}\n\n👤 {name}\n📞 {username}\n\n✅ Approved by {approver_name}"

            await context.bot.send_photo(
                chat_id=msg.chat_id,
                photo=msg.photo[-1].file_id,
                caption=text,
                message_thread_id=thread_id
            )

        del pending[key]

    elif data.startswith("album_"):
        mgid = data.replace("album_", "")

        if mgid not in albums:
            await query.edit_message_text("⛔ Already processed")
            return

        album = albums[mgid]

        for admin_id, message_id in album["admin_media"]:
            try:
                await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
            except:
                pass

        for admin_id, message_id in album["admin_msgs"]:
            try:
                await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
            except:
                pass

        user = album["user"]
        approver = query.from_user

        name = user.full_name
        username = f"@{user.username}" if user.username else "username байхгүй"
        approver_name = approver.full_name

        media = []
        first_msg = album["messages"][0]
        caption = first_msg.caption or ""

        final_caption = f"{caption}\n\n👤 {name}\n📞 {username}\n\n✅ Approved by {approver_name}"

        for i, m in enumerate(album["messages"]):
            if i == 0:
                media.append(InputMediaPhoto(
                    media=m.photo[-1].file_id,
                    caption=final_caption
                ))
            else:
                media.append(InputMediaPhoto(
                    media=m.photo[-1].file_id
                ))

        await context.bot.send_media_group(
            chat_id=album["chat_id"],
            media=media,
            message_thread_id=album["thread_id"]
        )

        del albums[mgid]

    elif data.startswith("reject_album_"):
        mgid = data.replace("reject_album_", "")

        if mgid in albums:
            album = albums[mgid]

            for admin_id, message_id in album["admin_media"]:
                try:
                    await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
                except:
                    pass

            for admin_id, message_id in album["admin_msgs"]:
                try:
                    await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
                except:
                    pass

            del albums[mgid]

    elif data.startswith("reject_"):
        key = data.replace("reject_", "")

        if key in pending:
            for admin_id, message_id in pending[key]["admin_msgs"]:
                try:
                    await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
                except:
                    pass

            del pending[key]


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle))
    app.add_handler(CallbackQueryHandler(button))

    import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

    app.run_polling()
