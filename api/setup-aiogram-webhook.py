from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import asyncio
from aiogram import Bot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен")
    BOT_TOKEN = "7559539951:AAG3SL-275Z0-4M24MUrA5p7feNd-SW1py4"  # Используем резервный токен

# URL для настройки вебхука
VERCEL_URL = os.environ.get("VERCEL_URL") or "v0-kenga-bur-assistant.vercel.app"
if not VERCEL_URL.startswith(("http://", "https://")):
    VERCEL_URL = f"https://{VERCEL_URL}"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для установки вебхука
async def set_webhook():
    webhook_url = f"{VERCEL_URL}/api/telegram-webhook"
    logger.info(f"Устанавливаем вебхук для aiogram на адрес: {webhook_url}")
    
    # Удаляем текущий вебхук
    logger.info("Удаляем текущий вебхук")
    await bot.delete_webhook()
    
    # Устанавливаем новый вебхук
    logger.info("Устанавливаем новый вебхук")
    result = await bot.set_webhook(url=webhook_url)
    
    # Получаем информацию о вебхуке
    logger.info("Получаем информацию о вебхуке")
    webhook_info = await bot.get_webhook_info()
    
    return {
        "success": result,
        "webhook_url": webhook_url,
        "webhook_info": {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections
        }
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Настраиваем вебхук и возвращаем информацию
            result = asyncio.run(set_webhook())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка при настройке вебхука: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e)
            }).encode('utf-8')) 