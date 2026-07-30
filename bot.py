import telebot
import requests
import re
import time

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🌍 *IP Геолокатор Бот*\n\n"
        "Отправь мне IP-адрес, и я покажу:\n"
        "📍 Страну, город, провайдера\n"
        "🗺️ Ссылку на Google Карты\n"
        "📡 Информацию о сети\n\n"
        "📌 Пример: `8.8.8.8`",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        "🤖 *Как пользоваться ботом:*\n\n"
        "1. Отправь любой IP-адрес\n"
        "2. Бот покажет страну, город, провайдера\n"
        "3. Нажми на ссылку в конце сообщения, чтобы открыть карту\n\n"
        "📌 *Пример:* `8.8.8.8`\n"
        "📌 *Команды:* `/start` `/help`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    ip = message.text.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат IP-адреса\nПример: `8.8.8.8`", parse_mode="Markdown")
        return
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone'
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить геолокацию.")
            return

        lat = data.get('lat')
        lon = data.get('lon')
        map_url = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

        result = (
            f"📍 *Геолокация IP: {ip}*\n\n"
            f"🌍 *Страна:* {data.get('country', 'Неизвестно')}\n"
            f"🏛️ *Регион:* {data.get('regionName', 'Неизвестно')}\n"
            f"🏙️ *Город:* {data.get('city', 'Неизвестно')}\n"
            f"📡 *Провайдер:* {data.get('isp', 'Неизвестно')}\n"
            f"🏢 *Организация:* {data.get('org', 'Неизвестно')}\n"
            f"🔢 *AS:* {data.get('as', 'Неизвестно')}\n"
            f"🌐 *Часовой пояс:* {data.get('timezone', 'Неизвестно')}\n"
            f"🗺️ *Координаты:* {lat}, {lon}"
        )

        if map_url:
            result += f"\n\n[🌍 Открыть на Google Картах]({map_url})"

        bot.reply_to(message, result, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏰ *Таймаут запроса.*\nПопробуй позже.", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Ошибка:* {str(e)[:100]}", parse_mode="Markdown")

print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
