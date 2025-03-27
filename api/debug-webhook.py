from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot
import asyncio

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для получения информации о боте и вебхуке
async def get_debug_info():
    try:
        # Получаем информацию о боте
        me = await bot.get_me()
        
        # Получаем информацию о вебхуке
        webhook_info = await bot.get_webhook_info()
        
        # Проверяем, есть ли ошибки в вебхуке
        has_webhook_errors = webhook_info.last_error_message is not None or webhook_info.last_error_date is not None
        
        # Проверяем, установлен ли вебхук
        is_webhook_set = webhook_info.url is not None and len(webhook_info.url) > 0
        
        # Проверяем, есть ли ожидающие обновления
        has_pending_updates = webhook_info.pending_update_count > 0
        
        return {
            "success": True,
            "botInfo": me.to_dict(),
            "webhookInfo": webhook_info.to_dict(),
            "diagnostics": {
                "hasWebhookErrors": has_webhook_errors,
                "isWebhookSet": is_webhook_set,
                "hasPendingUpdates": has_pending_updates
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Получаем отладочную информацию
            result = asyncio.run(get_debug_info())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

