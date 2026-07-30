import os
import re
import time
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================================
#  НАСТРОЙКИ
# ============================================================
TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
bot = telebot.TeleBot(TOKEN)

# Премиум-цены (в Telegram Stars)
PRICES = [telebot.types.LabeledPrice(label="Премиум на 30 дней", amount=50)]  # 50 Stars

# Хранилище (в реальном проекте используй БД)
user_consent = {}   # user_id: True/False (согласие)
user_premium = {}   # user_id: timestamp окончания подписки
user_data = {}      # user_id: данные

ADMIN_ID = 123456789  # ЗАМЕНИ НА СВОЙ ID

# ============================================================
#  FLASK ДЛЯ RENDER
# ============================================================
app = Flask(__name__)

@app.route('/')
def health():
    return "✅ Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ============================================================
#  АВТО-ПИНГ (НЕ ДАЁТ RENDER УСНУТЬ)
# ============================================================
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

# ============================================================
#  ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ
# ============================================================
PRIVACY_TEXT = """
📋 *Условия конфиденциальности*

Для работы бота мы собираем следующую информацию:
• Ваш IP-адрес (для определения геолокации)
• Ваш ID в Telegram (для статистики)

Эти данные используются только для:
• Показа геолокации по вашему IP
• Статистики использования бота

Мы НЕ передаём ваши данные третьим лицам.

Вы можете удалить свои данные командой /delete_data

Нажимая «Принимаю», вы соглашаетесь с этими условиями.
"""

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    if user_consent.get(user_id):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⭐ Премиум", callback_data="premium_info"))
        keyboard.add(InlineKeyboardButton("🌍 Моя геолокация", callback_data="my_ip"))
        keyboard.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
        bot.reply_to(
            message,
            "🌍 *IP Геолокатор Бот*\n\n"
            "Отправь мне IP-адрес, или выбери действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Принимаю", callback_data="accept"),
        InlineKeyboardButton("❌ Отказываюсь", callback_data="decline")
    )
    bot.reply_to(message, PRIVACY_TEXT, reply_markup=keyboard, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["accept", "decline"])
def handle_consent(call):
    user_id = call.message.chat.id
    if call.data == "accept":
        user_consent[user_id] = True
        bot.edit_message_text(
            "✅ Спасибо! Ты принял условия.\n\nТеперь отправь мне IP-адрес, или нажми /start",
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        bot.send_message(ADMIN_ID, f"🆕 Новый пользователь: {user_id}")
    else:
        user_consent[user_id] = False
        bot.edit_message_text(
            "❌ Ты отказался от условий.\n\nБот работает в ограниченном режиме.",
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
    bot.answer_callback_query(call.id)

# ============================================================
#  ПРЕМИУМ-ПОДПИСКА (Telegram Stars)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "premium_info")
def premium_info(call):
    user_id = call.message.chat.id
    status = "✅ Активна" if user_premium.get(user_id, 0) > time.time() else "❌ Не активна"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⭐ Купить за 50 Stars", callback_data="buy_premium"))
    bot.edit_message_text(
        f"⭐ *Премиум-подписка*\n\n"
        f"Статус: {status}\n\n"
        f"• Безлимит запросов\n"
        f"• История запросов\n"
        f"• Экспорт в CSV\n"
        f"• Приоритетная обработка\n\n"
        f"Цена: 50 Telegram Stars (≈ 30 дней)",
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def buy_premium(call):
    user_id = call.message.chat.id
    try:
        bot.send_invoice(
            chat_id=user_id,
            title="⭐ Премиум-подписка",
            description="30 дней безлимитных запросов",
            invoice_payload="premium_payload",
            provider_token="",  # Для Stars оставляем пустым
            currency="XTR",     # Telegram Stars
            prices=PRICES,
            start_parameter="premium",
            need_name=False,
            need_email=False,
            need_phone_number=False
        )
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    user_premium[user_id] = time.time() + 30 * 86400  # 30 дней
    bot.send_message(user_id, "⭐ Поздравляю! Премиум-подписка активирована на 30 дней!")

# ============================================================
#  ОСНОВНАЯ ЛОГИКА (ГЕОЛОКАЦИЯ)
# ============================================================
@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    user_id = message.chat.id
    ip = message.text.strip()

    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат IP. Пример: 8.8.8.8")
        return

    # Проверка премиума (для бесплатных — ограничение)
    is_premium = user_premium.get(user_id, 0) > time.time()
    if not is_premium and not user_consent.get(user_id):
        bot.reply_to(message, "⚠️ Прими условия конфиденциальности (/start) или купи премиум.")
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
            f"📍 *Геолокация IP: {ip}*\n\n"
            f"🌍 *Страна:* {data.get('country', 'Неизвестно')}\n"
            f"🏙️ *Город:* {data.get('city', 'Неизвестно')}\n"
            f"📡 *Провайдер:* {data.get('isp', 'Неизвестно')}\n"
            f"🗺️ *Координаты:* {lat}, {lon}"
        )
        if map_url:
            result += f"\n\n[🌍 Открыть на Google Картах]({map_url})"

        if is_premium:
            result += "\n\n⭐ Премиум-пользователь"

        bot.reply_to(message, result, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

# ============================================================
#  КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "🤖 *Команды:*\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/delete_data — удалить мои данные\n"
        "/my_data — показать мои данные\n"
        "/premium — статус подписки\n\n"
        "📌 Отправь IP-адрес, например 8.8.8.8",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['my_data'])
def my_data(message):
    user_id = message.chat.id
    data = user_data.get(user_id, {})
    if not data:
        bot.reply_to(message, "📭 Нет сохранённых данных.")
        return
    result = f"📊 *Твои данные:*\nIP: {data.get('ip')}\nСтрана: {data.get('country')}\nГород: {data.get('city')}"
    bot.reply_to(message, result, parse_mode="Markdown")

@bot.message_handler(commands=['delete_data'])
def delete_data(message):
    user_id = message.chat.id
    user_data.pop(user_id, None)
    bot.reply_to(message, "🧹 Данные удалены.")

@bot.message_handler(commands=['premium'])
def premium_status(message):
    user_id = message.chat.id
    is_premium = user_premium.get(user_id, 0) > time.time()
    status = "✅ Активна" if is_premium else "❌ Не активна"
    bot.reply_to(message, f"⭐ *Статус подписки:* {status}", parse_mode="Markdown")

# ============================================================
#  ЗАПУСК
# ============================================================
print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
