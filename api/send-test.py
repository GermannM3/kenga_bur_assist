from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot
import asyncio

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для отправки тестового сообщения
async def send_test_message(chat_id):
    try:
        message = await bot.send_message(
            chat_id=chat_id,
            text="Тестовое сообщение от бота. Если вы видите это сообщение, значит бот работает корректно!"
        )
        return {
            "success": True,
            "message_info": message.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Парсим JSON-данные
            data = json.loads(post_data.decode('utf-8'))
            chat_id = data.get('chat_id')
            
            if not chat_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Chat ID is required"}).encode('utf-8'))
                return
            
            # Отправляем тестовое сообщение
            result = asyncio.run(send_test_message(chat_id))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

