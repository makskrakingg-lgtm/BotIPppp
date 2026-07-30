import os
import re
import time
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
bot = telebot.TeleBot(TOKEN)

user_consent = {}
user_premium = {}
user_data = {}

ADMIN_ID = 8937690024

app = Flask(__name__)

@app.route('/')
def health():
    return "✅ Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

def keep_alive():
    url = os.environ.get("RENDER_EXTERNAL_URL", "https://botipppp-7.onrender.com")
    while True:
        try:
            requests.get(url, timeout=10)
            print("⏰ Пинг выполнен")
        except:
            pass
        time.sleep(180)

threading.Thread(target=keep_alive, daemon=True).start()

PRIVACY_TEXT = """
Условия конфиденциальности

Для работы бота мы собираем:
- Ваш IP-адрес (для геолокации)
- Ваш ID в Telegram (для статистики)

Данные используются только для:
- Показа геолокации по IP
- Статистики

Мы НЕ передаём данные третьим лицам.

Вы можете удалить свои данные командой /delete_data

Нажимая «Принимаю», вы соглашаетесь с этими условиями.
"""

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id

    if user_consent.get(user_id):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("⭐ Премиум", callback_data="premium_info"))
        keyboard.row(InlineKeyboardButton("🌍 Моя геолокация", callback_data="my_ip"))
        keyboard.row(InlineKeyboardButton("❓ Помощь", callback_data="help"))
        bot.reply_to(
            message,
            "🌍 IP Геолокатор Бот\n\nОтправь IP-адрес или выбери действие:",
            reply_markup=keyboard
        )
        return

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Принимаю", callback_data="accept"),
        InlineKeyboardButton("❌ Отказываюсь", callback_data="decline")
    )
    bot.reply_to(message, PRIVACY_TEXT, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id

    if call.data == "accept":
        user_consent[user_id] = True
        bot.edit_message_text(
            "✅ Спасибо! Ты принял условия.\n\nТеперь отправь мне IP-адрес, или нажми /start",
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.send_message(ADMIN_ID, f"🆕 Новый пользователь: {user_id}")
        bot.answer_callback_query(call.id)
        return

    if call.data == "decline":
        user_consent[user_id] = False
        bot.edit_message_text(
            "❌ Ты отказался от условий.\n\nБот работает в ограниченном режиме.",
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "premium_info":
        status = "✅ Активна" if user_premium.get(user_id, 0) > time.time() else "❌ Не активна"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("⭐ Купить за 50 Stars", callback_data="buy_premium"))
        bot.edit_message_text(
            f"⭐ Премиум-подписка\n\nСтатус: {status}\n\n- Безлимит запросов\n- История\n- Экспорт CSV\n- Приоритет\n\nЦена: 50 Stars (≈ 30 дней)",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "buy_premium":
        try:
            bot.send_invoice(
                chat_id=user_id,
                title="⭐ Премиум-подписка",
                description="30 дней безлимитных запросов",
                invoice_payload="premium_payload",
                provider_token="",
                currency="XTR",
                prices=[telebot.types.LabeledPrice(label="Премиум 30 дней", amount=50)],
                start_parameter="premium",
                need_name=False,
                need_email=False,
                need_phone_number=False
            )
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка: {e}")
        bot.answer_callback_query(call.id)
        return

    if call.data == "help":
        bot.edit_message_text(
            "🤖 Команды:\n/start - главное меню\n/help - помощь\n/delete_data - удалить данные\n/premium - статус подписки\n\nОтправь IP, например 8.8.8.8",
            chat_id=user_id,
            message_id=call.message.message_id
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "my_ip":
        try:
            ip = requests.get('https://api.ipify.org').text
            bot.send_message(user_id, f"🌍 Твой IP: {ip}")
        except:
            bot.send_message(user_id, "❌ Не удалось определить IP")
        bot.answer_callback_query(call.id)
        return

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    user_premium[user_id] = time.time() + 30 * 86400
    bot.send_message(user_id, "⭐ Премиум активирован на 30 дней!")

@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    user_id = message.chat.id
    ip = message.text.strip()

    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат. Пример: 8.8.8.8")
        return

    if not user_consent.get(user_id):
        bot.reply_to(message, "⚠️ Прими условия конфиденциальности: /start")
        return

    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone'
        resp = requests.get(url, timeout=8)
        data = resp.json()

        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить геолокацию.")
            return

        lat, lon = data.get('lat'), data.get('lon')
        map_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        result = (
            f"📍 Геолокация IP: {ip}\n\n"
            f"🌍 Страна: {data.get('country', 'Неизвестно')}\n"
            f"🏙️ Город: {data.get('city', 'Неизвестно')}\n"
            f"📡 Провайдер: {data.get('isp', 'Неизвестно')}\n"
            f"🗺️ Координаты: {lat}, {lon}"
        )
        if map_url:
            result += f"\n\nКарта: {map_url}"

        bot.reply_to(message, result)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "🤖 Команды:\n/start - главное меню\n/help - помощь\n/delete_data - удалить данные\n/premium - статус подписки\n\nОтправь IP, например 8.8.8.8"
    )

@bot.message_handler(commands=['delete_data'])
def delete_data(message):
    user_id = message.chat.id
    user_data.pop(user_id, None)
    bot.reply_to(message, "🧹 Данные удалены.")

@bot.message_handler(commands=['premium'])
def premium_status(message):
    user_id = message.chat.id
    status = "✅ Активна" if user_premium.get(user_id, 0) > time.time() else "❌ Не активна"
    bot.reply_to(message, f"⭐ Статус подписки: {status}")

print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
