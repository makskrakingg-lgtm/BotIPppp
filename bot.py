import os
import re
import time
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
bot = telebot.TeleBot(TOKEN)

CHANNEL_ID = -1003952347104
CHANNEL_LINK = "https://t.me/+nQ6nvWI_o6BjOTJi"
ADMIN_ID = 5667799165
FREE_LIMIT = 2

user_consent = {}
user_premium = {}
user_data = {}
search_mode = {}
search_history = {}
daily_requests = {}

promo_codes = {
    "MAXII": False,
    "VITAA": False
}

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

def keep_alive():
    url = os.environ.get("RENDER_EXTERNAL_URL", "https://botipppp-7.onrender.com")
    while True:
        try:
            requests.get(url, timeout=10)
            print("Ping done")
        except:
            pass
        time.sleep(180)

threading.Thread(target=keep_alive, daemon=True).start()

PRIVACY_TEXT = """
Conditions of confidentiality

For the bot to work, we collect:
- Your IP address (for geolocation)
- Your Telegram ID (for statistics)

Data is used only for:
- Showing geolocation by IP
- Statistics

We do NOT transfer data to third parties.

You can delete your data with the /delete_data command

By clicking "Accept", you agree to these terms.
"""

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def require_subscription(func):
    def wrapper(message):
        user_id = message.chat.id
        if not is_subscribed(user_id):
            keyboard = InlineKeyboardMarkup()
            keyboard.row(InlineKeyboardButton("Subscribe to channel", url=CHANNEL_LINK))
            keyboard.row(InlineKeyboardButton("Check subscription", callback_data="check_sub"))
            bot.reply_to(
                message,
                "Please subscribe to our channel to use the bot.\n\nAfter subscribing, click Check subscription.",
                reply_markup=keyboard
            )
            return
        return func(message)
    return wrapper

def check_limit(user_id):
    is_premium = user_premium.get(user_id, 0) > time.time()
    if is_premium:
        return True
    today = str(date.today())
    if user_id not in daily_requests or daily_requests[user_id]['date'] != today:
        daily_requests[user_id] = {'date': today, 'count': 0}
    if daily_requests[user_id]['count'] >= FREE_LIMIT:
        return False
    daily_requests[user_id]['count'] += 1
    return True

def main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Premium", callback_data="premium_info"))
    keyboard.row(InlineKeyboardButton("My IP", callback_data="my_ip"))
    keyboard.row(InlineKeyboardButton("Search IP", callback_data="search_ip"))
    keyboard.row(InlineKeyboardButton("History", callback_data="history"))
    keyboard.row(InlineKeyboardButton("Help", callback_data="help"))
    return keyboard

@bot.message_handler(commands=['start'])
@require_subscription
def send_welcome(message):
    user_id = message.chat.id
    if user_consent.get(user_id):
        bot.reply_to(message, "Choose action:", reply_markup=main_menu(user_id))
        return
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Accept", callback_data="accept"),
        InlineKeyboardButton("Decline", callback_data="decline")
    )
    bot.reply_to(message, PRIVACY_TEXT, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text(
            "Subscription confirmed! Now you can use the bot.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id, "Subscription confirmed!")
    else:
        bot.answer_callback_query(call.id, "You are not subscribed yet.", show_alert=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id
    is_premium = user_premium.get(user_id, 0) > time.time()

    if call.data == "accept":
        user_consent[user_id] = True
        try:
            user_ip = requests.get('https://api.ipify.org').text
        except:
            user_ip = "Unknown"
        user = bot.get_chat(user_id)
        username = user.username or "No username"
        first_name = user.first_name or "No name"
        bot.send_message(
            ADMIN_ID,
            f"New user accepted terms\n\nID: {user_id}\nName: {first_name}\nUsername: @{username}\nIP: {user_ip}\nTime: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        bot.edit_message_text(
            "Thank you! You have accepted the terms.\n\nNow choose an action:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "decline":
        user_consent[user_id] = False
        bot.edit_message_text(
            "You declined the terms.\n\nThe bot works in limited mode.",
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "back_to_menu":
        bot.edit_message_text(
            "Choose action:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "search_ip":
        if not user_consent.get(user_id):
            bot.answer_callback_query(call.id, "Please accept terms first /start", show_alert=True)
            return
        search_mode[user_id] = True
        bot.edit_message_text(
            "Enter IP address to search\n\nExample: 8.8.8.8\n\nOr press Back:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "history":
        history = search_history.get(user_id, [])
        if not history:
            bot.answer_callback_query(call.id, "No search history yet.", show_alert=True)
            return
        if not is_premium:
            today = date.today().strftime("%d.%m.%Y")
            history = [h for h in history if h['time'].startswith(today)]
        if not history:
            bot.answer_callback_query(call.id, "No requests today.", show_alert=True)
            return
        text = "Search history:\n\n"
        for i, entry in enumerate(history[-10:], 1):
            text += f"{i}. {entry['ip']} - {entry['time']}\n"
        if not is_premium:
            text += "\nPremium shows full history (not only today)"
        keyboard = InlineKeyboardMarkup()
        if is_premium:
            keyboard.row(InlineKeyboardButton("Clear history", callback_data="clear_history"))
        keyboard.row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            text,
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "clear_history":
        if not is_premium:
            bot.answer_callback_query(call.id, "Clear history is available only in premium!", show_alert=True)
            return
        search_history[user_id] = []
        bot.edit_message_text(
            "History cleared.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "premium_info":
        status = "Active" if is_premium else "Not active"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("Buy for 50 Stars", callback_data="buy_premium"))
        keyboard.row(InlineKeyboardButton("Enter promo code", callback_data="enter_promo"))
        keyboard.row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            f"Premium subscription\n\nStatus: {status}\n\nUnlimited requests (free - 2 per day)\nFull history (free - only today)\nVPN/proxy detection\nClear history\nPriority processing\n\nPrice: 50 Stars (~30 days)\nOr enter promo code:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "enter_promo":
        bot.edit_message_text(
            "Enter promo code as one message.\n\nExample: MAXII\n\nOr press Back:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "buy_premium":
        try:
            bot.send_invoice(
                chat_id=user_id,
                title="Premium subscription",
                description="30 days unlimited requests + VPN detection",
                invoice_payload="premium_payload",
                provider_token="",
                currency="XTR",
                prices=[telebot.types.LabeledPrice(label="Premium 30 days", amount=50)],
                start_parameter="premium",
                need_name=False,
                need_email=False,
                need_phone_number=False
            )
        except Exception as e:
            bot.send_message(user_id, f"Error: {e}")
        bot.answer_callback_query(call.id)
        return

    if call.data == "help":
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            "Help\n\nCommands:\n/start - main menu\n/help - help\n/delete_data - delete data\n/premium - subscription status\n\nFree: 2 requests per day\nPremium: unlimited, full history, VPN status",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "my_ip":
        try:
            ip = requests.get('https://api.ipify.org').text
            keyboard = InlineKeyboardMarkup()
            keyboard.row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
            bot.edit_message_text(
                f"Your IP: {ip}",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
        except:
            bot.edit_message_text(
                "Failed to determine IP",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
            )
        bot.answer_callback_query(call.id)
        return

@bot.message_handler(func=lambda message: message.text and message.text.isupper() and len(message.text) >= 3)
@require_subscription
def handle_promo(message):
    user_id = message.chat.id
    code = message.text.strip().upper()
    if code in promo_codes:
        if promo_codes[code] is False:
            user_premium[user_id] = time.time() + 30 * 86400
            promo_codes[code] = True
            bot.send_message(user_id, f"Promo code {code} activated! Premium for 30 days.")
            bot.send_message(user_id, "Choose action:", reply_markup=main_menu(user_id))
            bot.send_message(ADMIN_ID, f"Promo code {code} used by user {user_id}")
        else:
            bot.send_message(user_id, f"Promo code {code} has already been used.")
    else:
        if search_mode.get(user_id):
            pass
        else:
            bot.send_message(user_id, f"Promo code {code} not found.")

@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "You don't have permission.")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: /addpromo CODE")
        return
    code = args[1].upper()
    if code in promo_codes:
        bot.reply_to(message, f"Promo code {code} already exists.")
        return
    promo_codes[code] = False
    bot.reply_to(message, f"Promo code {code} added. Can be used once.")

@bot.message_handler(commands=['listpromo'])
def list_promo(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "You don't have permission.")
        return
    if not promo_codes:
        bot.reply_to(message, "No active promo codes.")
        return
    text = "Promo codes:\n\n"
    for code, used in promo_codes.items():
        status = "used" if used else "active"
        text += f"• {code} - {status}\n"
    bot.reply_to(message, text)

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    user_premium[user_id] = time.time() + 30 * 86400
    bot.send_message(user_id, "Premium activated for 30 days!")
    bot.send_message(user_id, "Choose action:", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda message: True)
@require_subscription
def handle_ip(message):
    user_id = message.chat.id
    if not search_mode.get(user_id):
        return
    ip = message.text.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "Invalid format. Example: 8.8.8.8")
        return
    if not user_consent.get(user_id):
        bot.reply_to(message, "Accept privacy policy: /start")
        return
    if not check_limit(user_id):
        bot.reply_to(message, f"You have used {FREE_LIMIT} free requests today.\n\nBuy premium for 50 Stars or enter promo code.")
        return
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone,proxy'
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('status') != 'success':
            bot.reply_to(message, "Failed to determine geolocation.")
            return
        is_premium = user_premium.get(user_id, 0) > time.time()
        if user_id not in search_history:
            search_history[user_id] = []
        search_history[user_id].append({
            'ip': ip,
            'time': datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        if len(search_history[user_id]) > 50:
            search_history[user_id] = search_history[user_id][-50:]
        lat, lon = data.get('lat'), data.get('lon')
        map_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None
        result = f"Geolocation of IP: {ip}\n\nCountry: {data.get('country', 'Unknown')}\nCity: {data.get('city', 'Unknown')}\nISP: {data.get('isp', 'Unknown')}\nCoordinates: {lat}, {lon}"
        if is_premium:
            proxy_status = data.get('proxy', False)
            vpn_text = "Yes (VPN/proxy)" if proxy_status else "No (regular IP)"
            result += f"\n\nVPN/proxy: {vpn_text}"
        else:
            result += "\n\nVPN status available in premium version"
        if map_url:
            result += f"\n\nMap: {map_url}"
        if not is_premium:
            remaining = FREE_LIMIT - daily_requests.get(user_id, {'count': 0})['count']
            result += f"\n\nRequests left today: {remaining} out of {FREE_LIMIT}"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("New search", callback_data="search_ip"))
        keyboard.row(InlineKeyboardButton("Main menu", callback_data="back_to_menu"))
        bot.reply_to(message, result, reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)[:100]}")

@bot.message_handler(commands=['help'])
@require_subscription
def send_help(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Back", callback_data="back_to_menu"))
    bot.reply_to(
        message,
        "Help\n\nCommands:\n/start - main menu\n/help - help\n/delete_data - delete data\n/premium - subscription status\n\nFree: 2 requests per day\nPremium: unlimited, full history, VPN status",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['delete_data'])
@require_subscription
def delete_data(message):
    user_id = message.chat.id
    user_data.pop(user_id, None)
    search_history.pop(user_id, None)
    daily_requests.pop(user_id, None)
    bot.reply_to(message, "Data and history deleted.")

@bot.message_handler(commands=['premium'])
@require_subscription
def premium_status(message):
    user_id = message.chat.id
    status = "Active" if user_premium.get(user_id, 0) > time.time() else "Not active"
    bot.reply_to(message, f"Premium status: {status}")

print("Bot started")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
