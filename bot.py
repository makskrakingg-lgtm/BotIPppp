import telebot
import requests
import re
import time
import sys

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Привет! Отправь мне IP-адрес.")

@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    ip = message.text.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат. Пример: 8.8.8.8")
        return
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone'
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить.")
            return
        result = (
            f"📍 *Геолокация IP: {ip}*\n\n"
            f"🌍 Страна: {data.get('country', '—')}\n"
            f"🏙️ Город: {data.get('city', '—')}\n"
            f"📡 Провайдер: {data.get('isp', '—')}\n"
            f"🗺️ Координаты: {data.get('lat', '—')}, {data.get('lon', '—')}"
        )
        bot.reply_to(message, result, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")

print("✅ Бот запущен")
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)
