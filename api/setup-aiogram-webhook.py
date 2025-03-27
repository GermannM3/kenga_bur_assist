from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import asyncio
import sys
import platform

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Вывод информации о системе для отладки
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
logger.info(f"Python version: {python_version}")
logger.info(f"Platform: {platform.platform()}")
logger.info(f"Environment: {os.environ.get('VERCEL_REGION', 'unknown')}")

try:
    from aiogram import Bot, version as aiogram_version
    logger.info(f"aiogram версия: {aiogram_version.__version__}")
    
    # Получение токена из переменных окружения
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        BOT_TOKEN = "7559539951:AAG3SL-275Z0-4M24MUrA5p7feNd-SW1py4"  # Используем резервный токен
    
    logger.info(f"Токен бота начинается с: {BOT_TOKEN[:8]}...")

    # URL для настройки вебхука
    VERCEL_URL = os.environ.get("VERCEL_URL") or "v0-kenga-bur-assistant.vercel.app"
    if not VERCEL_URL.startswith(("http://", "https://")):
        VERCEL_URL = f"https://{VERCEL_URL}"
    
    logger.info(f"URL для вебхука: {VERCEL_URL}")

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)

    # Функция для установки вебхука
    async def set_webhook():
        webhook_url = f"{VERCEL_URL}/api/telegram-webhook"
        logger.info(f"Устанавливаем вебхук для aiogram на адрес: {webhook_url}")
        
        try:
            # Удаляем текущий вебхук
            logger.info("Удаляем текущий вебхук")
            await bot.delete_webhook()
            
            # Устанавливаем новый вебхук
            logger.info("Устанавливаем новый вебхук")
            result = await bot.set_webhook(url=webhook_url)
            
            # Получаем информацию о вебхуке
            logger.info("Получаем информацию о вебхуке")
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Информация о вебхуке: {webhook_info}")
            
            # Тестируем отправку сообщения разработчику
            try:
                await bot.send_message(chat_id=5186134402, text=f"Настройка вебхука выполнена успешно: {webhook_url}")
                logger.info("Тестовое сообщение отправлено разработчику")
            except Exception as msg_error:
                logger.error(f"Ошибка при отправке тестового сообщения: {msg_error}")
            
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
                },
                "python_version": python_version,
                "status": "webhook_set_successfully"
            }
        except Exception as e:
            logger.error(f"Ошибка при настройке вебхука в функции set_webhook: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "python_version": python_version,
                "status": "webhook_setup_failed"
            }
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    
    # Заглушка функции при отсутствии aiogram
    async def set_webhook():
        return {
            "error": "Модуль aiogram не установлен или несовместим с текущей версией Python",
            "python_version": python_version,
            "status": "import_error"
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Настраиваем вебхук и возвращаем информацию
            logger.info("Запуск настройки вебхука")
            result = asyncio.run(set_webhook())
            logger.info(f"Результат настройки вебхука: {result}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                **result,
                "system_info": {
                    "python_version": python_version,
                    "platform": platform.platform(),
                    "vercel_region": os.environ.get('VERCEL_REGION', 'unknown'),
                    "environment_variables": {
                        key: "available" if os.environ.get(key) else "missing" 
                        for key in ["TELEGRAM_BOT_TOKEN", "VERCEL_URL", "BOT_SERVICE_URL"]
                    }
                }
            }, indent=2).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка при настройке вебхука: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e),
                "python_version": python_version,
                "traceback": f"{e.__class__.__name__}: {str(e)}"
            }).encode('utf-8')) 