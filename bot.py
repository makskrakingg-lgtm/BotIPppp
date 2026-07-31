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
📋 Условия конфиденциальности

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
            keyboard.row(InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_LINK))
            keyboard.row(InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
            bot.reply_to(
                message,
                "⚠️ Для использования бота необходимо подписаться на наш канал.\n\n"
                "После подписки нажми кнопку «Проверить подписку».",
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
    keyboard.row(InlineKeyboardButton("⭐ Премиум", callback_data="premium_info"))
    keyboard.row(InlineKeyboardButton("🌍 Моя геолокация", callback_data="my_ip"))
    keyboard.row(InlineKeyboardButton("🔍 Поиск IP", callback_data="search_ip"))
    keyboard.row(InlineKeyboardButton("📜 История", callback_data="history"))
    keyboard.row(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    return keyboard

@bot.message_handler(commands=['start'])
@require_subscription
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

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text(
            "✅ Спасибо за подписку! Теперь ты можешь пользоваться ботом.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена!")
    else:
        bot.answer_callback_query(call.id, "❌ Ты ещё не подписан.", show_alert=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id
    is_premium = user_premium.get(user_id, 0) > time.time()

    if call.data == "accept":
        user_consent[user_id] = True
        try:
            user_ip = requests.get('https://api.ipify.org').text
        except:
            user_ip = "Не удалось определить"
        user = bot.get_chat(user_id)
        username = user.username or "Нет юзернейма"
        first_name = user.first_name or "Нет имени"
        bot.send_message(
            ADMIN_ID,
            f"🆕 Новый пользователь принял условия\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Имя: {first_name}\n"
            f"🔗 Юзернейм: @{username}\n"
            f"🌍 IP: {user_ip}\n"
            f"🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        bot.edit_message_text(
            "✅ Спасибо! Ты принял условия.\n\nТеперь выбери действие:",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
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

    if call.data == "history":
        history = search_history.get(user_id, [])
        if not history:
            bot.answer_callback_query(call.id, "📭 У тебя пока нет истории поиска.", show_alert=True)
            return
        if not is_premium:
            today = date.today().strftime("%d.%m.%Y")
            history = [h for h in history if h['time'].startswith(today)]
        if not history:
            bot.answer_callback_query(call.id, "📭 За сегодня нет запросов.", show_alert=True)
            return
        text = "📜 История поиска:\n\n"
        for i, entry in enumerate(history[-10:], 1):
            text += f"{i}. {entry['ip']} — {entry['time']}\n"
        if not is_premium:
            text += "\n⭐ Премиум показывает всю историю (не только за сегодня)"
        keyboard = InlineKeyboardMarkup()
        if is_premium:
            keyboard.row(InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"))
        keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
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
            bot.answer_callback_query(call.id, "⭐ Очистка истории доступна только в премиум!", show_alert=True)
            return
        search_history[user_id] = []
        bot.edit_message_text(
            "🧹 История очищена.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "premium_info":
        status = "✅ Активна" if is_premium else "❌ Не активна"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("⭐ Купить за 50 Stars", callback_data="buy_premium"))
        keyboard.row(InlineKeyboardButton("🎟️ Ввести промокод", callback_data="enter_promo"))
        keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
        bot.edit_message_text(
            f"⭐ Премиум-подписка\n\nСтатус: {status}\n\n"
            "✅ Безлимит запросов (бесплатно — 2 в день)\n"
            "✅ Полная история (бесплатно — только сегодня)\n"
            "✅ Определение VPN/прокси\n"
            "✅ Очистка истории\n"
            "✅ Приоритетная обработка\n\n"
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
            "🤖 Помощь\n\n"
            "📌 Команды:\n"
            "/start — главное меню\n"
            "/help — помощь\n"
            "/delete_data — удалить данные\n"
            "/premium — статус подписки\n\n"
            "📊 Бесплатно: 2 запроса в день\n"
            "⭐ Премиум: безлимит, полная история, VPN-статус\n\n"
            "📞 По вопросам: @blackbox_research",
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

@bot.message_handler(func=lambda message: message.text and message.text.isupper() and len(message.text) >= 3)
@require_subscription
def handle_promo(message):
    user_id = message.chat.id
    code = message.text.strip().upper()
    if code in promo_codes:
        if promo_codes[code] is False:
            user_premium[user_id] = time.time() + 30 * 86400
            promo_codes[code] = True
            bot.send_message(
                user_id,
                f"🎉 Промокод {code} активирован! Премиум на 30 дней.\n\n"
                "Теперь у тебя безлимит запросов, полная история и VPN-статус!"
            )
            bot.send_message(user_id, "Выбери действие:", reply_markup=main_menu(user_id))
            bot.send_message(ADMIN_ID, f"✅ Промокод {code} использован пользователем {user_id}")
        else:
            bot.send_message(user_id, f"❌ Промокод {code} уже был использован.")
    else:
        if search_mode.get(user_id):
            pass
        else:
            bot.send_message(user_id, f"❌ Промокод {code} не найден.")

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

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    user_premium[user_id] = time.time() + 30 * 86400
    bot.send_message(user_id, "⭐ Премиум активирован на 30 дней!")
    bot.send_message(user_id, "Выбери действие:", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda message: True)
@require_subscription
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
    if not check_limit(user_id):
        bot.reply_to(
            message,
            f"⚠️ Ты использовал {FREE_LIMIT} бесплатных запросов сегодня.\n\n"
            f"Купи премиум за 50 Stars или введи промокод для безлимита."
        )
        return
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone,proxy'
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить геолокацию.")
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
        else:
            result += "\n\n⭐ VPN-статус доступен в премиум-версии"
        if map_url:
            result += f"\n\nКарта: {map_url}"
        if not is_premium:
            remaining = FREE_LIMIT - daily_requests.get(user_id, {'count': 0})['count']
            result += f"\n\n📊 Осталось запросов сегодня: {remaining} из {FREE_LIMIT}"
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("🔍 Новый поиск", callback_data="search_ip"))
        keyboard.row(InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_menu"))
        bot.reply_to(message, result, reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

@bot.message_handler(commands=['help'])
@require_subscription
def send_help(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
    bot.reply_to(
        message,
        "🤖 Помощь\n\n"
        "📌 Команды:\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/delete_data — удалить данные\n"
        "/premium — статус подписки\n\n"
        "📊 Бесплатно: 2 запроса в день\n"
        "⭐ Премиум: безлимит, полная история, VPN-статус\n\n"
        "📞 По вопросам: @blackbox_research",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['delete_data'])
@require_subscription
def delete_data(message):
    user_id = message.chat.id
    user_data.pop(user_id, None)
    search_history.pop(user_id, None)
    daily_requests.pop(user_id, None)
    bot.reply_to(message, "🧹 Данные и история удалены.")

@bot.message_handler(commands=['premium'])
@require_subscription
def premium_status(message):
    user_id = message.chat.id
    status = "✅ Активна" if user_premium.get(user_id, 0) > time.time() else "❌ Не активна"
    bot.reply_to(message, f"⭐ Статус подписки: {status}")

print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)
