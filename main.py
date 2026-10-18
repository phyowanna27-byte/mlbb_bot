import os
import re
import logging
import urllib.request
import urllib.parse
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = "8834166717:AAFfuD_ge9Xkfa48sp0iBaRXRpHALWaI5uk"
ADMIN_ID = 8863215122
ADMIN_USERNAME_URL = "https://t.me/MayLayGameStore"

DEFAULT_QR_URLS = [
    "https://i.ibb.co/6R2qZz7W/thai-qr.png",   # Thai PromptPay
    "https://i.ibb.co/VWVw4z4P/kpay-qr.jpg",    # KPay
    "https://i.ibb.co/sJcwtXv7/wave-qr.jpg"     # WavePay
]

# Weekly Pass စာရင်း
WEEKLY_PASSES = [
    ("Weekly Pass (1x)", "57 ฿ / 7,200 Ks"),
    ("Weekly Pass (2x)", "114 ฿ / 14,400 Ks"),
    ("Weekly Pass (3x)", "171 ฿ / 21,600 Ks"),
    ("Weekly Pass (4x)", "228 ฿ / 28,800 Ks"),
    ("Weekly Pass (5x)", "285 ฿ / 36,000 Ks"),
    ("Weekly Pass (6x)", "342 ฿ / 43,200 Ks"),
    ("Weekly Pass (7x)", "399 ฿ / 50,400 Ks"),
    ("Weekly Pass (8x)", "456 ฿ / 57,600 Ks"),
    ("Weekly Pass (9x)", "513 ฿ / 64,800 Ks"),
    ("Weekly Pass (10x)", "570 ฿ / 72,000 Ks"),
]

# Dia 2x Bonus
DIA_2X_LIST = [
    ("50 (+50 or +5 Bonus)", "32 ฿ / 3,800 Ks"),
    ("150 (+150 or +15 Bonus)", "88 ฿ / 11,000 Ks"),
    ("250 (+250 or +25 Bonus)", "140 ฿ / 17,700 Ks"),
    ("500 (+500 or +65 Bonus)", "288 ฿ / 36,300 Ks"),
]

# ပုံမှန်စိန် ဘတ်ဈေး
PRICES_THB = [
    ("86 Diamonds", "46 ฿"),
    ("172 Diamonds", "92 ฿"),
    ("275 Diamonds", "140 ฿"),
    ("343 Diamonds", "180 ฿"),
    ("429 Diamonds", "225 ฿"),
    ("565 Diamonds", "288 ฿"),
    ("600 Diamonds", "315 ฿"),
    ("706 Diamonds", "360 ฿"),
    ("878 Diamonds", "450 ฿"),
    ("963 Diamonds", "495 ฿"),
    ("1049 Diamonds", "540 ฿"),
    ("1135 Diamonds", "585 ฿"),
    ("1412 Diamonds", "720 ฿"),
    ("1584 Diamonds", "810 ฿"),
    ("1755 Diamonds", "900 ฿"),
    ("2195 Diamonds", "1080 ฿"),
    ("3244 Diamonds", "1620 ฿"),
    ("3688 Diamonds", "1790 ฿"),
    ("4394 Diamonds", "2150 ฿"),
    ("5532 Diamonds", "2690 ฿"),
    ("6238 Diamonds", "2990 ฿"),
    ("9288 Diamonds", "4390 ฿"),
    ("11483 Diamonds", "5490 ฿"),
    ("12976 Diamonds", "6190 ฿"),
]

# ပုံမှန်စိန် ကျပ်ဈေး
PRICES_MMK = [
    ("86 Diamonds", "5,800 Ks"),
    ("172 Diamonds", "11,500 Ks"),
    ("275 Diamonds", "17,700 Ks"),
    ("343 Diamonds", "22,700 Ks"),
    ("429 Diamonds", "28,200 Ks"),
    ("565 Diamonds", "36,300 Ks"),
    ("600 Diamonds", "39,300 Ks"),
    ("706 Diamonds", "45,300 Ks"),
    ("878 Diamonds", "56,800 Ks"),
    ("963 Diamonds", "62,000 Ks"),
    ("1049 Diamonds", "67,800 Ks"),
    ("1135 Diamonds", "73,500 Ks"),
    ("1412 Diamonds", "90,500 Ks"),
    ("1584 Diamonds", "102,000 Ks"),
    ("1755 Diamonds", "113,000 Ks"),
    ("2195 Diamonds", "137,000 Ks"),
    ("3244 Diamonds", "205,000 Ks"),
    ("3688 Diamonds", "229,000 Ks"),
    ("4394 Diamonds", "274,000 Ks"),
    ("5532 Diamonds", "345,000 Ks"),
    ("6238 Diamonds", "389,000 Ks"),
    ("9288 Diamonds", "573,000 Ks"),
    ("11483 Diamonds", "709,000 Ks"),
    ("12976 Diamonds", "799,000 Ks"),
]

PRICES_LIST = {}
for item, p in WEEKLY_PASSES:
    PRICES_LIST[item] = p
for item, p in DIA_2X_LIST:
    PRICES_LIST[item] = p
for i in range(len(PRICES_THB)):
    PRICES_LIST[PRICES_THB[i][0]] = f"{PRICES_THB[i][1]} / {PRICES_MMK[i][1]}"

PACKAGES = {
    "weekly": [item for item, _ in WEEKLY_PASSES],
    "dia2x": [item for item, _ in DIA_2X_LIST],
    "normal": [item for item, _ in PRICES_THB],
}

USER_ORDERS = {}

PAYMENT_TEXT = (
    "💳 <b>ငွေလွှဲရန် အကောင့်အချက်အလက်များနှင့် QR များ</b>\n\n"
    "🇹🇭 <b>PromptPay (Thai QR)</b>\n"
    "• အမည်: MR PHYO WANNA LINN\n"
    "• ဖုန်း: <code>061-xxx-0038</code>\n\n"
    "🇲🇲 <b>KPay</b>\n"
    "• အမည်: Ei Ei Phyu\n"
    "• အကောင့်: <code>*******1686</code>\n\n"
    "🇲🇲 <b>WavePay</b>\n"
    "• အမည်: Swan Pyae Sone\n"
    "• ဖုန်း: <code>09986422066</code>\n\n"
    "📌 <i>အပေါ်တွင် Scan ဖတ်နိုင်သော QR Code ၃ ခု ပို့ပေးထားပါသည်ခင်ဗျာ။</i>"
)

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

def get_bottom_keyboard():
    keyboard = [
        [KeyboardButton("🛒 အော်ဒါတင်မယ်"), KeyboardButton("💎 စိန်ဈေးနှုန်းများ")],
        [KeyboardButton("💳 ငွေလွှဲအကောင့်များ"), KeyboardButton("🔙 ပင်မမီနူး")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_inline_main_menu():
    keyboard = [
        [InlineKeyboardButton("💎 စိန်ဈေးနှုန်းများ", callback_data="btn_prices"),
         InlineKeyboardButton("💳 ငွေလွှဲအကောင့်များ", callback_data="btn_payment")],
        [InlineKeyboardButton("🛒 အော်ဒါတင်မယ်", callback_data="btn_order")],
        [InlineKeyboardButton("👤 Admin ဆက်သွယ်ရန်", url=ADMIN_USERNAME_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_price_category_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇹🇭 ထိုင်းဘတ်ဈေးနှုန်းများ", callback_data="view_p_thb")],
        [InlineKeyboardButton("🇲🇲 မြန်မာကျပ်ဈေးနှုန်းများ", callback_data="view_p_mmk")],
        [InlineKeyboardButton("🎟 Weekly Pass & Dia 2x", callback_data="view_p_special")],
        [InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_ORDERS.pop(user_id, None)
    msg = (
        "👋 မင်္ဂလာပါခင်ဗျာ၊ MLBB Game Top-up Reseller ဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်။\n\n"
        "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-"
    )
    await update.message.reply_text(msg, reply_markup=get_bottom_keyboard())
    await update.message.reply_text("👇 လိုအပ်ရာကို ရွေးချယ်ပေးပါ-", reply_markup=get_inline_main_menu())

async def send_payment_qr(chat_id, context: ContextTypes.DEFAULT_TYPE):
    media_group = [
        InputMediaPhoto(media=DEFAULT_QR_URLS[0], caption=PAYMENT_TEXT, parse_mode="HTML"),
        InputMediaPhoto(media=DEFAULT_QR_URLS[1]),
        InputMediaPhoto(media=DEFAULT_QR_URLS[2])
    ]
    await context.bot.send_media_group(chat_id=chat_id, media=media_group)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "btn_main_menu":
        USER_ORDERS.pop(user_id, None)
        await query.edit_message_text(
            "👋 မင်္ဂလာပါခင်ဗျာ၊ MLBB Game Top-up Reseller ဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်။\n\n"
            "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-",
            reply_markup=get_inline_main_menu()
        )

    elif data == "btn_prices":
        await query.edit_message_text(
            "💎 <b>ကြည့်ရှုလိုသော စိန်ဈေးနှုန်း အမျိုးအစားကို ရွေးချယ်ပါ-</b>",
            reply_markup=get_price_category_keyboard(),
            parse_mode="HTML"
        )

    elif data == "view_p_thb":
        text = "🇹🇭 <b>ထိုင်းဘတ်ဈေးနှုန်းများ (THB)</b> 🇹🇭\n\n"
        for item, price in PRICES_THB:
            text += f"🔹 <code>{item:<15}</code> : <b>{price}</b>\n"
        keyboard = [
            [InlineKeyboardButton("🇲🇲 ကျပ်ဈေးကြည့်မည်", callback_data="view_p_mmk"),
             InlineKeyboardButton("🎟 Pass / Dia 2x", callback_data="view_p_special")],
            [InlineKeyboardButton("🔙 နောက်သို့", callback_data="btn_prices")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "view_p_mmk":
        text = "🇲🇲 <b>မြန်မာကျပ်ဈေးနှုန်းများ (MMK)</b> 🇲🇲\n\n"
        for item, price in PRICES_MMK:
            text += f"🔹 <code>{item:<15}</code> : <b>{price}</b>\n"
        keyboard = [
            [InlineKeyboardButton("🇹🇭 ဘတ်ဈေးကြည့်မည်", callback_data="view_p_thb"),
             InlineKeyboardButton("🎟 Pass / Dia 2x", callback_data="view_p_special")],
            [InlineKeyboardButton("🔙 နောက်သို့", callback_data="btn_prices")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "view_p_special":
        text = "🎟 <b>Weekly Pass & Dia ၂ဆ ဘောနပ်စ် ဈေးနှုန်းများ</b> ✨\n\n"
        text += "🎟 <b>Weekly Diamond Passes:</b>\n"
        for item, price in WEEKLY_PASSES:
            text += f"• <code>{item}</code> : <code>{price}</code>\n"
        text += "\n💎 <b>Dia 2x (First Recharge Bonus):</b>\n"
        for item, price in DIA_2X_LIST:
            text += f"• <code>{item}</code> : <code>{price}</code>\n"
        keyboard = [
            [InlineKeyboardButton("🇹🇭 ဘတ်ဈေး", callback_data="view_p_thb"),
             InlineKeyboardButton("🇲🇲 ကျပ်ဈေး", callback_data="view_p_mmk")],
            [InlineKeyboardButton("🔙 နောက်သို့", callback_data="btn_prices")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "btn_payment":
        await send_payment_qr(query.message.chat_id, context)

    elif data == "btn_order":
        keyboard = [
            [InlineKeyboardButton("🎟 Weekly Pass (1x ~ 10x)", callback_data="cat_weekly")],
            [InlineKeyboardButton("💎 Dia ၂ဆ (Bonus)", callback_data="cat_dia2x")],
            [InlineKeyboardButton("💎 ပုံမှန်စိန်ဈေး", callback_data="cat_normal")],
            [InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]
        ]
        await query.edit_message_text(
            "🛒 <b>ဝယ်ယူလိုသော ပက်ကေ့ချ် အမျိုးအစားကို ရွေးချယ်ပါ-</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
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
            "📦 <b>ဝယ်ယူမည့် အထုပ်/ပမာဏကို ရွေးချယ်ပါ-</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif data.startswith("pkg_"):
        selected_item = data.replace("pkg_", "")
        price_info = PRICES_LIST.get(selected_item, "")
        USER_ORDERS[user_id] = {"item": selected_item, "price": price_info, "state": "AWAIT_ID"}
        
        cancel_kb = [[InlineKeyboardButton("🔙 မီနူးသို့ ပြန်သွားမည်", callback_data="btn_main_menu")]]
        await query.edit_message_text(
            f"✅ ရွေးချယ်ထားသော ပစ္စည်း: <b>{selected_item}</b>\n\n"
            f"🎮 ကျေးဇူးပြု၍ သင်၏ <b>MLBB UID နှင့် Zone ID</b> ကို ရိုက်ပို့ပေးပါခင်ဗျာ။\n"
            f"(ဥပမာ - <code>95480598 2500</code> သို့မဟုတ် <code>95480598(2500)</code>)",
            reply_markup=InlineKeyboardMarkup(cancel_kb),
            parse_mode="HTML"
        )

    elif data.startswith("adm_ok_"):
        cust_id = int(data.replace("adm_ok_", ""))
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ <b>အတည်ပြုပြီးပါပြီ - စိန်ထည့်ပေးပြီးပါပြီ</b>",
            parse_mode="HTML"
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
    text = (update.message.text or "").strip()

    # ခလုတ်စာသားများကို စစ်ဆေးခြင်း
    if "ပင်မမီနူး" in text or text in ["/start", "/menu"]:
        USER_ORDERS.pop(user_id, None)
        await update.message.reply_text(
            "👋 မင်္ဂလာပါခင်ဗျာ၊ ပင်မ Menu သို့ ပြန်လည်ရောက်ရှိပါပြီ-",
            reply_markup=get_inline_main_menu()
        )
        return

    if "စိန်ဈေးနှုန်းများ" in text:
        await update.message.reply_text(
            "💎 <b>ကြည့်ရှုလိုသော စိန်ဈေးနှုန်း အမျိုးအစားကို ရွေးချယ်ပါ-</b>",
            reply_markup=get_price_category_keyboard(),
            parse_mode="HTML"
        )
        return

    if "ငွေလွှဲအကောင့်များ" in text:
        await send_payment_qr(update.message.chat_id, context)
        return

    if "အော်ဒါတင်မယ်" in text:
        keyboard = [
            [InlineKeyboardButton("🎟 Weekly Pass (1x ~ 10x)", callback_data="cat_weekly")],
            [InlineKeyboardButton("💎 Dia ၂ဆ (Bonus)", callback_data="cat_dia2x")],
            [InlineKeyboardButton("💎 ပုံမှန်စိန်ဈေး", callback_data="cat_normal")],
            [InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]
        ]
        await update.message.reply_text(
            "🛒 <b>ဝယ်ယူလိုသော ပက်ကေ့ချ် အမျိုးအစားကို ရွေးချယ်ပါ-</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    # ID ဖတ်သည့် အဆင့်
    if user_id in USER_ORDERS and USER_ORDERS[user_id].get("state") == "AWAIT_ID":
        match = re.search(r"(\d{5,12})\s*[\(\[\{]?\s*(\d{3,6})\s*[\)\]\}]?", text)
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
                f"🎮 <b>MLBB အကောင့် အချက်အလက်</b>\n"
                f"• IGN: <code>{ign}</code>\n"
                f"• Server: <code>{server}</code>\n"
                f"• UID: <code>{uid} ({zone})</code>\n"
                f"• ပစ္စည်း: <b>{item_name}</b>\n"
                f"• ကျသင့်ငွေ: <code>{item_price}</code>\n\n"
                f"💳 <b>ငွေလွှဲရန် အောက်ပါ QR များဖြင့် Scan ဖတ်နိုင်ပါသည်-</b>\n"
                f"1️⃣ 🇹🇭 PromptPay (MR PHYO WANNA LINN)\n"
                f"2️⃣ 🇲🇲 KPay (Ei Ei Phyu)\n"
                f"3️⃣ 🇲🇲 WavePay (Swan Pyae Sone)\n\n"
                f"📌 <i>ငွေလွှဲပြီးပါက ဤနေရာတွင် ငွေလွှဲစလစ်ပုံ ပို့ပေးပါခင်ဗျာ။</i>"
            )

            media_group = [
                InputMediaPhoto(media=DEFAULT_QR_URLS[0], caption=info_text, parse_mode="HTML"),
                InputMediaPhoto(media=DEFAULT_QR_URLS[1]),
                InputMediaPhoto(media=DEFAULT_QR_URLS[2])
            ]
            await update.message.reply_media_group(media=media_group)
        else:
            await update.message.reply_text(
                "⚠️ ID ပုံစံ မှားယွင်းနေပါသည်။ ဥပမာ <code>95480598 2500</code> သို့မဟုတ် <code>95480598(2500)</code> ဟု ရိုက်ပို့ပေးပါ။\n\n"
                "မီနူးသို့ ပြန်သွားလိုပါက အောက်က <b>'🔙 ပင်မမီနူး'</b> ကို နှိပ်ပါခင်ဗျာ။",
                parse_mode="HTML"
            )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in USER_ORDERS and USER_ORDERS[user_id].get("state") == "AWAIT_SLIP":
        order = USER_ORDERS[user_id]
        photo_file = update.message.photo[-1].file_id

        admin_caption = (
            f"🛒 <b>အော်ဒါအသစ် ရောက်ရှိပါသည်!</b>\n\n"
            f"👤 ကာစတမ်မာ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"🎮 IGN: <code>{order['ign']}</code>\n"
            f"🌐 Server: <code>{order['server']}</code>\n"
            f"🆔 UID: <code>{order['uid']} ({order['zone']})</code>\n"
            f"📦 ပစ္စည်း: <b>{order['item']}</b>\n"
            f"💰 ကျသင့်ငွေ: <code>{order.get('price', '')}</code>\n\n"
            f"စလစ်စစ်ဆေးပြီးပါက အတည်ပြုခလုတ်ကို နှိပ်ပါ-"
        )

        admin_keyboard = [[InlineKeyboardButton("✅ စိန်ထည့်ပြီး အတည်ပြုမည်", callback_data=f"adm_ok_{user_id}")]]

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file,
            caption=admin_caption,
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="HTML"
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
