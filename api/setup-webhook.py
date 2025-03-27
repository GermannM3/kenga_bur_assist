from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot
import asyncio

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для установки вебхука
async def set_webhook(url):
    webhook_url = f"{url}/api/telegram"
    
    # Удаляем текущий вебхук
    await bot.delete_webhook()
    
    # Устанавливаем новый вебхук
    result = await bot.set_webhook(webhook_url)
    
    # Получаем информацию о вебхуке
    webhook_info = await bot.get_webhook_info()
    
    return {
        "success": result,
        "webhook_url": webhook_url,
        "webhook_info": webhook_info.to_dict()
    }

# Функция для получения информации о вебхуке
async def get_webhook_info():
    webhook_info = await bot.get_webhook_info()
    me = await bot.get_me()
    return {
        "status": "ok",
        "bot_info": me.to_dict(),
        "webhook_info": webhook_info.to_dict()
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Парсим JSON-данные
            data = json.loads(post_data.decode('utf-8'))
            url = data.get('url')
            
            if not url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "URL is required"}).encode('utf-8'))
                return
            
            # Устанавливаем вебхук
            result = asyncio.run(set_webhook(url))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
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
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

