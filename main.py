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

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8863215122"))
SHEET_ID = "1Z-a2t1EBZGe8R4BUwm5-zo4Ss_6IWfPAES_TR9VL7cI"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Global temporary state for customer orders
USER_ORDERS = {}

# MLBB Packages Definition
PACKAGES = {
    "weekly": [f"Weekly Pass {i}x" for i in range(1, 11)],
    "dia2x": [
        "50 + 50 Diamonds",
        "100 + 100 Diamonds",
        "250 + 250 Diamonds",
        "500 + 500 Diamonds",
        "1000 + 1000 Diamonds",
    ],
    "starlight": ["Normal Starlight", "Premium Starlight"],
    "twilight": ["Twilight Pass"],
    "epic": ["Epic Monthly Pass"],
    "elite": ["Elite Weekly Pass"],
    "normal": [
        "50+5 Diamonds", "150+15 Diamonds", "250+25 Diamonds", "500+65 Diamonds",
        "86 Diamonds", "172 Diamonds", "257 Diamonds", "344 Diamonds",
        "429 Diamonds", "514 Diamonds", "600 Diamonds", "706 Diamonds",
        "792 Diamonds", "963 Diamonds", "1,412 Diamonds", "2,195 Diamonds",
        "2,901 Diamonds", "3,688 Diamonds", "4,394 Diamonds", "5,532 Diamonds",
        "6,238 Diamonds", "7,376 Diamonds", "7,727 Diamonds", "9,288 Diamonds (HOT)",
        "12,976 Diamonds", "14,820 Diamonds", "18,576 Diamonds",
    ],
}

def get_sheet_prices():
    """Google Sheet ထဲမှ ဈေးနှုန်းများကို အချိန်နှင့်တပြေးညီ ဆွဲယူခြင်း"""
    prices = {}
    try:
        req = urllib.request.Request(SHEET_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            lines = [line.decode("utf-8") for line in resp.readlines()]
            reader = csv.DictReader(lines)
            for row in reader:
                item = row.get("Item_Name", "").strip()
                price = row.get("Price", "").strip()
                if item and price:
                    prices[item] = price
    except Exception as e:
        logging.error(f"Error fetching sheet: {e}")
    return prices

def check_mlbb_id(uid, zone):
    """isan.eu.org API ဖြင့် IGN နှင့် Server စစ်ဆေးခြင်း"""
    try:
        url = f"https://api.isan.eu.org/nickname/ml?id={uid}&zone={zone}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("success"):
                ign = data.get("name", "Unknown")
                server = "TH (ထိုင်း)" if zone.startswith("2") or zone.startswith("3") else "MM (မြန်မာ)"
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

# Command /start or /menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 မင်္ဂလာပါခင်ဗျာ၊ MLBB Game Top-up Reseller ဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်။\n\n"
        "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-"
    )
    await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())

# Callback Query Handler
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "btn_main_menu":
        await query.edit_message_text(
            "အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် အလွယ်တကူ စစ်ဆေးဝယ်ယူနိုင်ပါသည်-",
            reply_markup=get_main_menu_keyboard()
        )

    elif data == "btn_prices":
        prices = get_sheet_prices()
        if not prices:
            text = "💎 Sheet ထဲတွင် ဈေးနှုန်းများ မဖြည့်ရသေးပါခင်ဗျာ။"
        else:
            text = "💎 **MLBB စိန်ဈေးနှုန်းများ** 💎\n\n"
            for item, price in prices.items():
                text += f"• {item} : `{price}`\n"
        keyboard = [[InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "btn_payment":
        text = (
            "💳 **ငွေလွှဲရန် အကောင့်အချက်အလက်များ**\n\n"
            "🇹🇭 **PromptPay (Thai QR)**\n"
            "• အမည်: MR PHYO WANNA LINN\n"
            "• Mobile: 061-xxx-0038 (Bangkok Bank)\n\n"
            "🇲🇲 **KPay**\n"
            "• အမည်: Ei Ei Phyu\n"
            "• နံပါတ်: `*******1686`\n\n"
            "🇲🇲 **WavePay**\n"
            "• အမည်: Swan Pyae Sone\n"
            "• နံပါတ်: `09986422066`\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 မီနူးသို့", callback_data="btn_main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "btn_order":
        keyboard = [
            [InlineKeyboardButton("🎟 Weekly Pass", callback_data="cat_weekly"),
             InlineKeyboardButton("💎 Dia ၂ဆ", callback_data="cat_dia2x")],
            [InlineKeyboardButton("🌟 Starlight Card", callback_data="cat_starlight"),
             InlineKeyboardButton("🛡 Twilight Pass", callback_data="cat_twilight")],
            [InlineKeyboardButton("👑 Epic Monthly", callback_data="cat_epic"),
             InlineKeyboardButton("⚡ Elite Weekly Pass", callback_data="cat_elite")],
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
        USER_ORDERS[user_id] = {"item": selected_item, "state": "AWAIT_ID"}
        await query.edit_message_text(
            f"✅ သင်ရွေးချယ်ထားသော ပစ္စည်း: **{selected_item}**\n\n"
            f"🎮 ကျေးဇူးပြု၍ သင်၏ **MLBB UID နှင့် Zone ID** ကို ရိုက်ပို့ပေးပါခင်ဗျာ။\n"
            f"(ဥပမာ ပုံစံ - `95480598 2500` သို့မဟုတ် `95480598 (2500)`)"
        )

    # Admin Order Approval
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

# Customer Message Handler (UID & Zone ID)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""

    if user_id in USER_ORDERS and USER_ORDERS[user_id].get("state") == "AWAIT_ID":
        match = re.search(r"(\d{6,12})\s*[\(\[]?(\d{3,6})[\)\]]?", text)
        if match:
            uid, zone = match.group(1), match.group(2)
            ign, server = check_mlbb_id(uid, zone)
            if not ign:
                ign = "စစ်ဆေး၍မရပါ (အကောင့်မှန်ကန်ကြောင်း ပြန်စစ်ပါ)"
                server = "Unknown"

            USER_ORDERS[user_id]["uid"] = uid
            USER_ORDERS[user_id]["zone"] = zone
            USER_ORDERS[user_id]["ign"] = ign
            USER_ORDERS[user_id]["server"] = server
            USER_ORDERS[user_id]["state"] = "AWAIT_SLIP"

            info_text = (
                f"🎮 **MLBB အကောင့် အချက်အလက်**\n"
                f"• IGN: `{ign}`\n"
                f"• Server: `{server}`\n"
                f"• UID: `{uid} ({zone})`\n"
                f"• ပစ္စည်း: **{USER_ORDERS[user_id]['item']}**\n\n"
                f"💳 **ငွေလွှဲရန် အောက်ပါ QR များဖြင့် Scan ဖတ်နိုင်ပါသည်-**\n"
                f"1️⃣ 🇹🇭 Thai PromptPay (MR PHYO WANNA LINN)\n"
                f"2️⃣ 🇲🇲 KPay (Ei Ei Phyu - `*******1686`)\n"
                f"3️⃣ 🇲🇲 WavePay (Swan Pyae Sone - `09986422066`)\n\n"
                f"📌 *ငွေလွှဲပြီးပါက ဤနေရာတွင် ငွေလွှဲစလစ် (Screenshot ပုံ) ကို ပို့ပေးပါခင်ဗျာ။*"
            )

            # Send 3 QR Photos (PromptPay, KPay, WavePay)
            media_group = []
            if os.path.exists("thai_qr.jpg"):
                media_group.append(InputMediaPhoto(open("thai_qr.jpg", "rb"), caption=info_text, parse_mode="Markdown"))
            if os.path.exists("kpay_qr.jpg"):
                caption_for_kpay = "" if media_group else info_text
                media_group.append(InputMediaPhoto(open("kpay_qr.jpg", "rb"), caption=caption_for_kpay, parse_mode="Markdown"))
            if os.path.exists("wave_qr.jpg"):
                caption_for_wave = "" if media_group else info_text
                media_group.append(InputMediaPhoto(open("wave_qr.jpg", "rb"), caption=caption_for_wave, parse_mode="Markdown"))

            if media_group:
                await update.message.reply_media_group(media=media_group)
            else:
                await update.message.reply_text(info_text, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ ID ပုံစံ မှားယွင်းနေပါသည်။ ဥပမာ `95480598 2500` ပုံစံဖြင့် သေချာ ပြန်ရိုက်ပို့ပေးပါခင်ဗျာ။")

# Customer Slip Photo Handler
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
            f"📦 ပစ္စည်း: **{order['item']}**\n\n"
            f"စလစ်စစ်ဆေးပြီးပါက အောက်ပါခလုတ်ကို နှိပ်ပါ-"
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
            "✅ ငွေလွှဲစလစ် လက်ခံရရှိပါပြီခင်ဗျာ။\nAdmin မှ စစ်ဆေးအတည်ပြုပြီးသည်နှင့် စိန်ထည့်သွင်းပေးပါမည်။ ခေတ္တစောင့်ဆိုင်းပေးပါခင်ဗျာ။"
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
