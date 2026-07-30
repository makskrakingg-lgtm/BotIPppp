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
search_mode = {}

# Хранилище промокодов: {код: True/False (использован)}
promo_codes = {
    "MAXII": False  # False = ещё не использован
}

ADMIN_ID = 8937690024  # твой Telegram ID

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

# ============================================================
#  ГЛАВНОЕ МЕНЮ
# ============================================================
def main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("⭐ Премиум", callback_data="premium_info"))
    keyboard.row(InlineKeyboardButton("🌍 Моя геолокация", callback_data="my_ip"))
    keyboard.row(InlineKeyboardButton("🔍 Поиск IP", callback_data="search_ip"))
    keyboard.row(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id

    if user_consent.get(user_id):
        bot.reply_to(
            message,
            "🌍 IP Геолокатор Бот\n\nВыбери действие:",
            reply_markup=main_menu(user_id)
        )
        return

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Принимаю", callback_data="accept"),
        InlineKeyboardButton("❌ Отказываюсь", callback_data="decline")
    )
    bot.reply_to(message, PRIVACY_TEXT, reply_markup=keyboard)

# ============================================================
#  ОБРАБОТЧИК КНОПОК
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id

    if call.data == "accept":
        user_consent[user_id] = True
        bot.edit_message_text(
            "✅ Спасибо! Ты принял условия.\n\nТеперь выбери действие:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
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

    if call.data == "back_to_menu":
        bot.edit_message_text(
            "🌍 IP Геолокатор Бот\n\nВыбери действие:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "search_ip":
        if not user_consent.get(user_id):
            bot.answer_callback_query(call.id, "⚠️ Сначала прими условия /start", show_alert=True)
            return
        search_mode[user_id] = True
        bot.edit_message_text(
            "🔍 Введи IP-адрес для поиска\n\nПример: 8.8.8.8\n\nИли нажми «Назад» для возврата:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "premium_info":
        status = "✅ Активна" if user_premium.get(user_id, 0) > time.time() else "❌ Не активна"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("⭐ Купить за 50 Stars", callback_data="buy_premium"))
        keyboard.row(InlineKeyboardButton("🎟️ Ввести промокод", callback_data="enter_promo"))
        keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.edit_message_text(
            f"⭐ Премиум-подписка\n\nСтатус: {status}\n\n"
            "✅ Безлимит запросов\n"
            "✅ История запросов\n"
            "✅ Экспорт в CSV\n"
            "✅ Приоритетная обработка\n"
            "✅ Определение VPN/прокси\n\n"
            "Цена: 50 Stars (≈ 30 дней)\n"
            "Или введи промокод:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "enter_promo":
        bot.edit_message_text(
            "🎟️ Введи промокод одним сообщением.\n\nПример: MAXII\n\nИли нажми «Назад»:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "buy_premium":
        try:
            bot.send_invoice(
                chat_id=user_id,
                title="⭐ Премиум-подписка",
                description="30 дней безлимитных запросов + определение VPN",
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
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.edit_message_text(
            "🤖 Команды:\n/start - главное меню\n/help - помощь\n/delete_data - удалить данные\n/premium - статус подписки\n\nОтправь IP, например 8.8.8.8",
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
            keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
            bot.edit_message_text(
                f"🌍 Твой IP: {ip}",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
        except:
            bot.edit_message_text(
                "❌ Не удалось определить IP",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
            )
        bot.answer_callback_query(call.id)
        return

# ============================================================
#  ОБРАБОТКА ПРОМОКОДОВ
# ============================================================
@bot.message_handler(func=lambda message: message.text and message.text.isupper() and len(message.text) >= 3)
def handle_promo(message):
    user_id = message.chat.id
    code = message.text.strip().upper()

    # Проверяем, в режиме ли ввода промокода (по последнему сообщению от бота)
    # Просто проверяем, есть ли код в списке
    if code in promo_codes:
        if promo_codes[code] is False:
            # Активируем премиум
            user_premium[user_id] = time.time() + 30 * 86400
            promo_codes[code] = True  # помечаем как использованный
            bot.send_message(
                user_id,
                f"🎉 Промокод {code} активирован! Премиум на 30 дней.\n\nТеперь ты видишь VPN-статус IP."
            )
            bot.send_message(user_id, "Выбери действие:", reply_markup=main_menu(user_id))
            bot.send_message(ADMIN_ID, f"✅ Промокод {code} использован пользователем {user_id}")
        else:
            bot.send_message(user_id, f"❌ Промокод {code} уже был использован.")
    else:
        # Если код не найден, но пользователь не в режиме поиска — просто игнорируем
        if search_mode.get(user_id):
            # Если он в режиме поиска, то это не промокод, а IP
            pass
        else:
            bot.send_message(user_id, f"❌ Промокод {code} не найден.")

# ============================================================
#  ДОБАВЛЕНИЕ ПРОМОКОДОВ (ТОЛЬКО ДЛЯ АДМИНА)
# ============================================================
@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав для этой команды.")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: /addpromo КОД")
        return

    code = args[1].upper()
    if code in promo_codes:
        bot.reply_to(message, f"❌ Промокод {code} уже существует.")
        return

    promo_codes[code] = False
    bot.reply_to(message, f"✅ Промокод {code} добавлен. Теперь его можно использовать один раз.")

# ============================================================
#  ПЛАТЕЖИ
# ============================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    user_premium[user_id] = time.time() + 30 * 86400
    bot.send_message(user_id, "⭐ Премиум активирован на 30 дней! Теперь ты видишь VPN-статус IP.")
    bot.send_message(user_id, "Выбери действие:", reply_markup=main_menu(user_id))

# ============================================================
#  ГЕОЛОКАЦИЯ
# ============================================================
@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    user_id = message.chat.id

    if not search_mode.get(user_id):
        return

    ip = message.text.strip()

    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат. Пример: 8.8.8.8")
        return

    if not user_consent.get(user_id):
        bot.reply_to(message, "⚠️ Прими условия конфиденциальности: /start")
        return

    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone,proxy'
        resp = requests.get(url, timeout=8)
        data = resp.json()

        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить геолокацию.")
            return

        lat, lon = data.get('lat'), data.get('lon')
        map_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        is_premium = user_premium.get(user_id, 0) > time.time()

        result = (
            f"📍 Геолокация IP: {ip}\n\n"
            f"🌍 Страна: {data.get('country', 'Неизвестно')}\n"
            f"🏙️ Город: {data.get('city', 'Неизвестно')}\n"
            f"📡 Провайдер: {data.get('isp', 'Неизвестно')}\n"
            f"🗺️ Координаты: {lat}, {lon}"
        )

        if is_premium:
            proxy_status = data.get('proxy', False)
            vpn_text = "🔒 Да (VPN/прокси)" if proxy_status else "✅ Нет (обычный IP)"
            result += f"\n\n🛡️ VPN/прокси: {vpn_text}"

        if map_url:
            result += f"\n\nКарта: {map_url}"

        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("🔍 Новый поиск", callback_data="search_ip"))
        keyboard.row(InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_menu"))

        bot.reply_to(message, result, reply_markup=keyboard)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

# ============================================================
#  КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "🤖 Команды:\n/start - главное меню\n/help - помощь\n/delete_data - удалить данные\n/premium - статус подписки",
        reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
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

@bot.message_handler(commands=['listpromo'])
def list_promo(message):
    user_id = message.chat.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ У тебя нет прав.")
        return
    if not promo_codes:
        bot.reply_to(message, "📭 Нет активных промокодов.")
        return
    text = "📋 Список промокодов:\n\n"
    for code, used in promo_codes.items():
        status = "✅ использован" if used else "🟢 активен"
        text += f"• {code} — {status}\n"
    bot.reply_to(message, text)

print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
