import os
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

BOT_TOKEN = "8834166717:AAFfuD_ge9Xkfa48sp0iBaRXRpHALWaI5uk"
ADMIN_ID = 8863215122

PENDING_ORDERS = {}
AWAITING_SLIP_ORDERS = {}

logging.basicConfig(level=logging.INFO)

# Render Web Service Live ဖြစ်စေရန် Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def handle_group_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()

    if text.startswith(".ml"):
        parts = text.split()
        if len(parts) != 4:
            await msg.reply_text(
                "❌ Format မှားယွင်းနေပါသည်။\nအသုံးပြုပုံ- `.ml <UID> <ZoneID> <Diamonds>`\nဥပမာ- `.ml 95480598 2500 165`",
                parse_mode="Markdown"
            )
            return

        _, uid, zone, amount = parts
        buyer_name = msg.from_user.full_name or msg.from_user.first_name
        chat_id = msg.chat_id

        confirm_msg = await msg.reply_text(
            f"⏳ *အော်ဒါလက်ခံရရှိပါပြီ*\n"
            f"UID: `{uid} ({zone})`\n"
            f"Order: `{amount} Diamonds`\n"
            f"Admin စစ်ဆေးအတည်ပြုနေပါသည်...",
            parse_mode="Markdown"
        )

        order_key = f"{chat_id}_{confirm_msg.message_id}"
        PENDING_ORDERS[order_key] = {
            "uid": uid,
            "zone": zone,
            "amount": amount,
            "chat_id": chat_id,
            "reply_to_msg_id": confirm_msg.message_id,
            "buyer": buyer_name
        }

        admin_keyboard = [
            [
                InlineKeyboardButton("📸 စိန်သွင်းပြီးပြီ (စလစ်ပုံပို့မည်)", callback_data=f"slip_{order_key}"),
                InlineKeyboardButton("✅ ပုံမပါဘဲ အတည်ပြုမည်", callback_data=f"done_{order_key}")
            ],
            [
                InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"reject_{order_key}")
            ]
        ]
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🚨 *အော်ဒါအသစ် ရောက်လာပါသည်!*\n\n"
                f"👤 Buyer: {buyer_name}\n"
                f"🎮 UID: `{uid}`\n"
                f"🌐 Zone: `{zone}`\n"
                f"💎 Diamonds: `{amount}`\n\n"
                f"စိန်ထည့်ပေးပြီးပါက အောက်ပါခလုတ်မှ ရွေးချယ်ပါ-"
            ),
            reply_
