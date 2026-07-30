import os
import re
import requests
from flask import Flask, request
import telebot

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
WEBHOOK_URL = "https://botipppp-7.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Бот работает! Отправь мне IP-адрес.")

@bot.message_handler(func=lambda message: True)
def handle_ip(message):
    ip = message.text.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        bot.reply_to(message, "❌ Неверный формат IP. Пример: 8.8.8.8")
        return
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,as,timezone'
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('status') != 'success':
            bot.reply_to(message, "❌ Не удалось определить геолокацию.")
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

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_data = request.get_data().decode('UTF-8')
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            print(f"Ошибка: {e}")
            return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "✅ Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
