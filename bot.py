import os
import requests
import re
from flask import Flask, request
import telebot

TOKEN = "8937690024:AAGmYikGTmqwFIHPnt1utvYn1hh8CHAXHU0"
WEBHOOK_URL = "https://botipppp-7.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот работает ✅")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('UTF-8'))
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            print(f"Ошибка: {e}")
            return '', 200
    return '', 400

@app.route('/')
def index():
    return "✅ Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
