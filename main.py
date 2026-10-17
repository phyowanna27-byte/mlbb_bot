import os
import logging
import threading
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8834166717:AAFfuD_ge9Xkfa48sp0iBaRXRpHALWaI5uk"
ADMIN_ID = 8863215122

PENDING_ORDERS = {}
AWAITING_SLIP = {}

logging.basicConfig(level=logging.INFO)

def check_mlbb_account(uid, zone):
    try:
        url = f"https://api.isan.eu.org/nickname/ml?id={uid}&zone={zone}"
        res = requests.get(url, timeout=7).json()
        if res.get("success"):
            name = res.get("name", "Unknown")
            country = res.get("country", "")
            
            # Country Check logic
            if country == "MM" or "myanmar" in country.lower():
                server_text = "🇲🇲 Myanmar Server"
            elif country == "TH" or "thailand" in country.lower():
                server_text = "🇹🇭 Thailand Server"
            elif country:
                server_text = f"🌐 {country} Server"
            else:
                server_text = "🌐 Global Server"
                
            return True, name, server_text
        else:
            return False, None, None
    except Exception as e:
        logging.error(f"API Error: {e}")
        return True, "Check Failed", "Server Unknown"

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    text = msg.text.strip()
    if text.startswith(".ml"):
        parts = text.split()
        if len(parts) != 4:
            await msg.reply_text("❌ Format မှားနေပါသည်။\nဥပမာ- `.ml 95480598 2500 165`", parse_mode="Markdown")
            return
        _, uid, zone, amount = parts
        buyer = msg.from_user.full_name or msg.from_user.first_name
        chat_id = msg.chat_id

        # Check Account & Server
        status, ign_name, server_info = check_mlbb_account(uid, zone)
        if not status:
            await msg.reply_text("❌ MLBB Account ID / Zone ID မှားယွင်းနေပါသည်။ သေချာပြန်စစ်ပေးပါ။")
            return

        confirm = await msg.reply_text(
            f"⏳ *အော်ဒါလက်ခံရရှိပါပြီ*\n"
            f"👤 IGN: `{ign_name}`\n"
            f"🌐 Server: *{server_info}*\n"
            f"🎮 UID: `{uid} ({zone})`\n"
            f"💎 Order: `{amount} Diamonds`\n\n"
            f"Admin စစ်ဆေးအတည်ပြုနေပါသည်...",
            parse_mode="Markdown"
        )
        
        key = f"{chat_id}_{confirm.message_id}"
        PENDING_ORDERS[key] = {
            "uid": uid, "zone": zone, "amount": amount,
            "chat_id": chat_id, "mid": confirm.message_id, "buyer": buyer,
            "ign": ign_name, "server": server_info
        }
        kb = [
            [
                InlineKeyboardButton("📸 စလစ်ပို့မည်", callback_data=f"slip_{key}"),
                InlineKeyboardButton("✅ ပုံမပါ အတည်ပြုမည်", callback_data=f"done_{key}")
            ],
            [InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"rej_{key}")]
        ]
        text_admin = (
            f"🚨 *အော်ဒါအသစ် ရောက်ရှိ!*\n"
            f"👤 ကာစတမ်မာ: {buyer}\n"
            f"🎮 IGN: `{ign_name}`\n"
            f"🌐 Server: *{server_info}*\n"
            f"🆔 UID: `{uid} ({zone})`\n"
            f"💎 Order: `{amount}` Diamonds"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text_admin, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, key = query.data.split("_", 1)
    order = PENDING_ORDERS.get(key)
    if not order:
        await query.edit_message_text("❌ အော်ဒါ မရှိတော့ပါ။")
        return

    now = datetime.now().strftime("%I:%M%p\n%d.%m.%Y")
    sn = f"S{datetime.now().strftime('%y%m%d%H%M%S')}ZUWE"

    if action == "slip":
        AWAITING_SLIP[ADMIN_ID] = key
        await query.edit_message_text(f"📸 `{order['ign']}` ({order['server']}) အတွက် စလစ်ပုံ ပို့ပေးပါ-")
    elif action == "done":
        rpt = (
            "==== Transaction Report ====\n"
            f"IGN    : {order['ign']}\n"
            f"Server : {order['server']}\n"
            f"UID    : {order['uid']} ({order['zone']})\n"
            f"Buyer  : {order['buyer']}\n"
            f"Order  : {order['amount']} Diamonds\n"
            f"SN     :\n{sn}\n"
            f"Time   : {now}\n"
            "===== MLBB SUCCESS =====\nStatus : စိန်ထည့်သွင်းပြီးပါပြီ ✅"
        )
        await context.bot.edit_message_text(chat_id=order["chat_id"], message_id=order["mid"], text=rpt)
        await query.edit_message_text(f"✅ UID `{order['uid']}` အောင်မြင်စွာ အတည်ပြုပြီးပါပြီ။")
        del PENDING_ORDERS[key]
    elif action == "rej":
        await context.bot.edit_message_text(chat_id=order["chat_id"], message_id=order["mid"], text=f"❌ UID `{order['uid']}` အော်ဒါ ပယ်ဖျက်လိုက်ပါသည်။")
        await query.edit_message_text(f"❌ UID `{order['uid']}` အော်ဒါကို ငြင်းပယ်လိုက်ပါပြီ။")
        del PENDING_ORDERS[key]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_admin = update.message.from_user.id
    if uid_admin != ADMIN_ID or uid_admin not in AWAITING_SLIP:
        return
    key = AWAITING_SLIP.pop(uid_admin)
    order = PENDING_ORDERS.pop(key, None)
    if not order:
        await update.message.reply_text("❌ အော်ဒါ မရှိတော့ပါ။")
        return

    now = datetime.now().strftime("%I:%M%p\n%d.%m.%Y")
    sn = f"S{datetime.now().strftime('%y%m%d%H%M%S')}ZUWE"
    rpt = (
        "==== Transaction Report ====\n"
        f"IGN    : {order['ign']}\n"
        f"Server : {order['server']}\n"
        f"UID    : {order['uid']} ({order['zone']})\n"
        f"Buyer  : {order['buyer']}\n"
        f"Order  : {order['amount']} Diamonds\n"
        f"SN     :\n{sn}\n"
        f"Time   : {now}\n"
        "===== MLBB SUCCESS =====\nStatus : စိန်ထည့်သွင်းပြီးပါပြီ ✅"
    )
    photo = update.message.photo[-1].file_id
    await context.bot.send_photo(chat_id=order["chat_id"], photo=photo, caption=rpt, reply_to_message_id=order["mid"])
    await update.message.reply_text(f"✅ UID `{order['uid']}` အား စလစ်ပုံဖြင့် Group ထဲ ပို့ပေးပြီးပါပြီ။")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_order))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    app.run_polling()
