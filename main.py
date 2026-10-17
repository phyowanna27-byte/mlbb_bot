import logging
from datetime import datetime
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
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, order_key = query.data.split("_", 1)
    order = PENDING_ORDERS.get(order_key)

    if not order:
        await query.edit_message_text("❌ ဤအော်ဒါ ပြီးဆုံးသွားပြီ (သို့မဟုတ်) ရှာမတွေ့တော့ပါ။")
        return

    now = datetime.now().strftime("%I:%M%p\n%d.%m.%Y")
    serial_no = f"S{datetime.now().strftime('%y%m%d%H%M%S')}ZUWE"

    if action == "slip":
        AWAITING_SLIP_ORDERS[ADMIN_ID] = order_key
        await query.edit_message_text(
            f"📸 *UID: {order['uid']} အတွက် စိန်သွင်းပြီးကြောင်း စလစ် (သို့မဟုတ်) ကြော်ငြာပုံကို ဒီ Chat ထဲသို့ ပို့ပေးပါ-*"
        )

    elif action == "done":
        report = (
            "==== Transaction Report ====\n"
            f"UID    : {order['uid']} ({order['zone']})\n"
            f"Name   : {order['buyer']}\n"
            f"Order  : {order['amount']} Diamonds\n"
            f"SN     :\n{serial_no}\n"
            f"Time   : {now}\n"
            "===== MLBB SUCCESS =====\n"
            "Status : စိန်ထည့်သွင်းပြီးပါပြီ ✅"
        )

        await context.bot.edit_message_text(
            chat_id=order["chat_id"],
            message_id=order["reply_to_msg_id"],
            text=report
        )
        await query.edit_message_text(f"✅ UID `{order['uid']}` ကို အောင်မြင်စွာ အတည်ပြုလိုက်ပါပြီ။")
        del PENDING_ORDERS[order_key]

    elif action == "reject":
        await context.bot.edit_message_text(
            chat_id=order["chat_id"],
            message_id=order["reply_to_msg_id"],
            text=f"❌ UID `{order['uid']}` အတွက် အော်ဒါ မအောင်မြင်ပါ။ (ငြင်းပယ်သည်)"
        )
        await query.edit_message_text(f"❌ UID `{order['uid']}` အော်ဒါကို ပယ်ဖျက်လိုက်ပါပြီ။")
        del PENDING_ORDERS[order_key]

async def handle_admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return

    if user_id in AWAITING_SLIP_ORDERS:
        order_key = AWAITING_SLIP_ORDERS[user_id]
        order = PENDING_ORDERS.get(order_key)

        if not order:
            await update.message.reply_text("❌ အော်ဒါသက်တမ်း ကုန်သွားပါပြီ။")
            del AWAITING_SLIP_ORDERS[user_id]
            return

        now = datetime.now().strftime("%I:%M%p\n%d.%m.%Y")
        serial_no = f"S{datetime.now().strftime('%y%m%d%H%M%S')}ZUWE"

        report = (
            "==== Transaction Report ====\n"
            f"UID    : {order['uid']} ({order['zone']})\n"
            f"Name   : {order['buyer']}\n"
            f"Order  : {order['amount']} Diamonds\n"
            f"SN     :\n{serial_no}\n"
            f"Time   : {now}\n"
            "===== MLBB SUCCESS =====\n"
            "Status : စိန်ထည့်သွင်းပြီးပါပြီ ✅"
        )

        photo_id = update.message.photo[-1].file_id

        await context.bot.send_photo(
            chat_id=order["chat_id"],
            photo=photo_id,
            caption=report,
            reply_to_message_id=order["reply_to_msg_id"]
        )

        await update.message.reply_text(f"✅ အော်ဒါ UID `{order['uid']}` ကို စလစ်ပုံနှင့်အတူ Group ထဲ ပို့ပေးပြီးပါပြီ။")

        del PENDING_ORDERS[order_key]
        del AWAITING_SLIP_ORDERS[user_id]

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_group_order))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_admin_photo))
    app.run_polling()
