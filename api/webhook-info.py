from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot
import asyncio

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для получения информации о вебхуке
async def get_webhook_info():
    try:
        webhook_info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {
            "status": "ok",
            "bot_info": me.to_dict(),
            "webhook_info": webhook_info.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Получаем информацию о вебхуке
            result = asyncio.run(get_webhook_info())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

