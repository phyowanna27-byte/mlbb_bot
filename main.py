import os
import re
import csv
import logging
import urllib.request
import urllib.parse
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Configurations
BOT_TOKEN = "8834166717:AAFfuD_ge9Xkfa48sp0iBaRXRpHALWaI5uk"
ADMIN_ID = 8863215122

# Cloud Image URLs for QR Codes
DEFAULT_QR_URLS = [
    "https://i.ibb.co/6R2qZz7W/thai-qr.png",   # Thai PromptPay
    "https://i.ibb.co/VWVw4z4P/kpay-qr.jpg",    # KPay
    "https://i.ibb.co/sJcwtXv7/wave-qr.jpg"     # WavePay
]

# ဈေးနှုန်းစာရင်းအသစ်များ (ဘတ်ဈေး နှင့် ကျပ်ဈေး)
PRICES_LIST = {
    "Weekly Pass (၁ ပတ်စာ)": "57 ฿ / 7,200 Ks",
    "86 Diamonds": "46 ฿ / 5,800 Ks",
    "172 Diamonds": "92 ฿ / 11,500 Ks",
    "275 Diamonds": "140 ฿ / 17,700 Ks",
    "343 Diamonds": "180 ฿ / 22,700 Ks",
    "429 Diamonds": "225 ฿ / 28,200 Ks",
    "565 Diamonds": "288 ฿ / 36,300 Ks",
    "600 Diamonds": "315 ฿ / 39,300 Ks",
    "706 Diamonds": "360 ฿ / 45,300 Ks",
    "878 Diamonds": "450 ฿ / 56,800 Ks",
    "963 Diamonds": "495 ฿ / 62,000 Ks",
    "1049 Diamonds": "540 ฿ / 67,800 Ks",
    "1135 Diamonds": "585 ฿ / 73,500 Ks",
    "1412 Diamonds": "720 ฿ / 90,500 Ks",
    "1584 Diamonds": "810 ฿ / 102,000 Ks",
    "1755 Diamonds": "900 ฿ / 113,000 Ks",
    "2195 Diamonds": "1080 ฿ / 137,000 Ks",
    "3244 Diamonds": "1620 ฿ / 205,000 Ks",
    "3688 Diamonds": "1790 ฿ / 229,000 Ks",
    "4394 Diamonds": "2150 ฿ / 274,000 Ks",
    "5532 Diamonds": "2690 ฿ / 345,000 Ks",
    "6238 Diamonds": "2990 ฿ / 389,000 Ks",
    "9288 Diamonds": "4390 ฿ / 573,000 Ks",
    "11483 Diamonds": "5490 ฿ / 709,000 Ks",
    "12976 Diamonds": "6190 ฿ / 799,000 Ks",
    "50 (+50 or +5 Bonus)": "32 ฿ / 3,800 Ks",
    "150 (+150 or +15 Bonus)": "88 ฿ / 11,000 Ks",
    "250 (+250 or +25 Bonus)": "140 ฿ / 17,700 Ks",
    "500 (+500 or +65 Bonus)": "288 ฿ / 36,300 Ks",
}

USER_ORDERS = {}

PACKAGES = {
    "weekly": ["Weekly Pass (၁ ပတ်စာ)"],
    "dia2x": [
        "50 (+50 or +5 Bonus)",
        "150 (+150 or +15 Bonus)",
        "250 (+250 or +25 Bonus)",
        "500 (+500 or +65 Bonus)",
    ],
    "normal": [
        "86 Diamonds", "172 Diamonds", "275 Diamonds", "343 Diamonds",
        "429 Diamonds", "565 Diamonds", "600 Diamonds", "706 Diamonds",
        "878 Diamonds", "963 Diamonds", "1049 Diamonds", "1135 Diamonds",
        "1412 Diamonds", "1584 Diamonds", "1755 Diamonds", "2195 Diamonds",
        "3244 Diamonds", "3688 Diamonds", "4394 Diamonds", "5532 Diamonds",
        "6238 Diamonds", "9288 Diamonds", "11483 Diamonds", "12976 Diamonds",
    ],
}

def check_mlbb_id(uid, zone):
    try:
        url = f"https://api.isan.eu.org/nickname/ml?id={uid}&zone={zone}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("success"):
                ign = data.get("name", "Unknown")
                server = "TH Server" if zone.startswith("2") or zone.startswith("3") else "MM Server"
                return ign, server
    except Exception as e:
        logging.error(f"API Error: {e}")
    return None, None

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💎 စိန်ဈေးနှုန်းများ", callback_data="btn_prices"),
         InlineKeyboardButton("💳 ငွေလွှဲအကောင့်များ", callback_data="btn_payment")],
        [InlineKeyboardButton("🛒 အော်ဒါတင်မယ်", callback_data="btn_order"),
         InlineKeyboardButton("👤 Admin ဆက်သွယ်ရန်", url="https://t.me/Ayar_reseller_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 မင်္ဂလာပါခင်ဗျာ၊ MLBB Game Top-up Reseller ဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်။\n\n"
        "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-"
    )
    await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "btn_main_menu":
        await query.edit_message_text(
            "👋 မင်္ဂလာပါခင်ဗျာ၊ MLBB Game Top-up Reseller ဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်။\n\n"
            "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-",
            reply_markup=get_main_menu_keyboard()
        )

    elif data == "btn_prices":
        text = "💎 **MLBB စိန်ဈေးနှုန်းများ (ဘတ်ဈေး / ကျပ်ဈေး)** 💎\n\n"
        for item, price in PRICES_LIST.items():
            text += f"• **{item}** : `{price}`\n"
        keyboard = [[InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "btn_payment":
        text = (
            "💳 **ငွေလွှဲရန် အကောင့်အချက်အလက်များ**\n\n"
            "🇹🇭 **PromptPay (Thai QR)**\n"
            "• အမည်: MR PHYO WANNA LINN\n"
            "• ဖုန်း: `061-xxx-0038`\n\n"
            "🇲🇲 **KPay**\n"
            "• အမည်: Ei Ei Phyu\n"
            "• အကောင့်: `*******1686`\n\n"
            "🇲🇲 **WavePay**\n"
            "• အမည်: Swan Pyae Sone\n"
            "• ဖုန်း: `09986422066`\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "btn_order":
        keyboard = [
            [InlineKeyboardButton("🎟 Weekly Pass", callback_data="cat_weekly"),
             InlineKeyboardButton("💎 Dia ၂ဆ (Bonus)", callback_data="cat_dia2x")],
            [InlineKeyboardButton("💎 ပုံမှန်စိန်ဈေး", callback_data="cat_normal")],
            [InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]
        ]
        await query.edit_message_text(
            "🛒 **ဝယ်ယူလိုသော ပက်ကေ့ချ် အမျိုးအစားကို ရွေးချယ်ပါ-**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        items = PACKAGES.get(cat_key, [])
        keyboard = []
        row = []
        for item in items:
            row.append(InlineKeyboardButton(item, callback_data=f"pkg_{item}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 နောက်သို့", callback_data="btn_order")])
        await query.edit_message_text(
            "📦 **ဝယ်ယူမည့် အထုပ်/ပမာဏကို ရွေးချယ်ပါ-**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("pkg_"):
        selected_item = data.replace("pkg_", "")
        price_info = PRICES_LIST.get(selected_item, "")
        USER_ORDERS[user_id] = {"item": selected_item, "price": price_info, "state": "AWAIT_ID"}
        await query.edit_message_text(
            f"✅ သင်ရွေးချယ်ထားသော ပစ္စည်း: **{selected_item}**\n"
            f"💰 ဈေးနှုန်း: `{price_info}`\n\n"
            f"🎮 ကျေးဇူးပြု၍ သင်၏ **MLBB UID နှင့် Zone ID** ကို ရိုက်ပို့ပေးပါခင်ဗျာ။\n"
            f"(ဥပမာ - `95480598 2500`)"
        )

    elif data.startswith("adm_ok_"):
        cust_id = int(data.replace("adm_ok_", ""))
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ **အတည်ပြုပြီးပါပြီ - စိန်ထည့်ပေးပြီးပါပြီ**",
            parse_mode="Markdown"
        )
        try:
            await context.bot.send_message(
                chat_id=cust_id,
                text="🎉 သင်၏ MLBB အော်ဒါအတွက် စိန်ထည့်သွင်းခြင်း အောင်မြင်စွာ ပြီးစီးပါပြီခင်ဗျာ။ အားပေးမှုကို ကျေးဇူးတင်ပါသည်!"
            )
        except Exception:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""

    if user_id in USER_ORDERS and USER_ORDERS[user_id].get("state") == "AWAIT_ID":
        match = re.search(r"(\d{6,12})\s*[\(\[]?(\d{3,6})[\)\]]?", text)
        if match:
            uid, zone = match.group(1), match.group(2)
            ign, server = check_mlbb_id(uid, zone)
            if not ign:
                ign = "စစ်ဆေးမရပါ"
                server = "Unknown"

            USER_ORDERS[user_id]["uid"] = uid
            USER_ORDERS[user_id]["zone"] = zone
            USER_ORDERS[user_id]["ign"] = ign
            USER_ORDERS[user_id]["server"] = server
            USER_ORDERS[user_id]["state"] = "AWAIT_SLIP"

            item_name = USER_ORDERS[user_id]["item"]
            item_price = USER_ORDERS[user_id].get("price", "")

            info_text = (
                f"🎮 **MLBB အကောင့် အချက်အလက်**\n"
                f"• IGN: `{ign}`\n"
                f"• Server: `{server}`\n"
                f"• UID: `{uid} ({zone})`\n"
                f"• ပစ္စည်း: **{item_name}**\n"
                f"• ကျသင့်ငွေ: `{item_price}`\n\n"
                f"💳 **ငွေလွှဲရန် အောက်ပါ QR များဖြင့် Scan ဖတ်နိုင်ပါသည်-**\n"
                f"1️⃣ 🇹🇭 PromptPay (MR PHYO WANNA LINN)\n"
                f"2️⃣ 🇲🇲 KPay (Ei Ei Phyu)\n"
                f"3️⃣ 🇲🇲 WavePay (Swan Pyae Sone)\n\n"
                f"📌 *ငွေလွှဲပြီးပါက ဤနေရာတွင် ငွေလွှဲစလစ်ပုံ ပို့ပေးပါခင်ဗျာ။*"
            )

            media_group = [
                InputMediaPhoto(media=DEFAULT_QR_URLS[0], caption=info_text, parse_mode="Markdown"),
                InputMediaPhoto(media=DEFAULT_QR_URLS[1]),
                InputMediaPhoto(media=DEFAULT_QR_URLS[2])
            ]
            await update.message.reply_media_group(media=media_group)
        else:
            await update.message.reply_text("⚠️ ID ပုံစံ မှားယွင်းနေပါသည်။ ဥပမာ `95480598 2500` ဟု ရိုက်ပို့ပေးပါ။")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in USER_ORDERS and USER_ORDERS[user_id].get("state") == "AWAIT_SLIP":
        order = USER_ORDERS[user_id]
        photo_file = update.message.photo[-1].file_id

        admin_caption = (
            f"🛒 **အော်ဒါအသစ် ရောက်ရှိပါသည်!**\n\n"
            f"👤 ကာစတမ်မာ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"🎮 IGN: `{order['ign']}`\n"
            f"🌐 Server: `{order['server']}`\n"
            f"🆔 UID: `{order['uid']} ({order['zone']})`\n"
            f"📦 ပစ္စည်း: **{order['item']}**\n"
            f"💰 ကျသင့်ငွေ: `{order.get('price', '')}`\n\n"
            f"စလစ်စစ်ဆေးပြီးပါက အတည်ပြုခလုတ်ကို နှိပ်ပါ-"
        )

        admin_keyboard = [[InlineKeyboardButton("✅ စိန်ထည့်ပြီး အတည်ပြုမည်", callback_data=f"adm_ok_{user_id}")]]

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file,
            caption=admin_caption,
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            "✅ ငွေလွှဲစလစ် လက်ခံရရှိပါပြီခင်ဗျာ။ Admin မှ စစ်ဆေးပြီး စိန်ထည့်သွင်းပေးပါမည်။"
        )
        USER_ORDERS.pop(user_id, None)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
