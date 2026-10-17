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

# Render Web Service Live ဖြစ်နေစေရန် Web Server အတိုလေး run ပေးခြင်း
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
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

        _, uid, zone
