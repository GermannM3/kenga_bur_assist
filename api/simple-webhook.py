from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import sys
import platform
import urllib.request
import urllib.parse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Вывод информации о системе для отладки
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
logger.info(f"Python version: {python_version}")
logger.info(f"Platform: {platform.platform()}")

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

# Функция для прямого вызова Telegram Bot API
def telegram_api_request(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    
    if data:
        data = json.dumps(data).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
    else:
        data = None
        headers = {}
    
    req = urllib.request.Request(url, data=data, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"Ошибка при вызове Telegram API: {e}")
        return {"ok": False, "error": str(e)}

# Функция для установки вебхука
def set_webhook():
    webhook_url = f"{VERCEL_URL}/api/simple-webhook"
    logger.info(f"Устанавливаем вебхук на адрес: {webhook_url}")
    
    # Удаляем текущий вебхук
    delete_result = telegram_api_request("deleteWebhook")
    logger.info(f"Результат удаления вебхука: {delete_result}")
    
    # Устанавливаем новый вебхук
    set_result = telegram_api_request("setWebhook", {"url": webhook_url})
    logger.info(f"Результат установки вебхука: {set_result}")
    
    # Получаем информацию о вебхуке
    webhook_info = telegram_api_request("getWebhookInfo")
    logger.info(f"Информация о вебхуке: {webhook_info}")
    
    # Отправляем тестовое сообщение
    message_result = telegram_api_request("sendMessage", {
        "chat_id": 5186134402,
        "text": f"Вебхук настроен: {webhook_url}\nВерсия Python: {python_version}"
    })
    logger.info(f"Результат отправки тестового сообщения: {message_result}")
    
    return {
        "success": set_result.get("ok", False),
        "webhook_url": webhook_url,
        "webhook_info": webhook_info.get("result", {}),
        "test_message": message_result.get("ok", False),
        "python_version": python_version
    }

# Функция для обработки обновлений от Telegram
def process_update(update_data):
    logger.info(f"Получено обновление от Telegram: {update_data}")
    
    # Базовая обработка сообщений
    if "message" in update_data and "text" in update_data["message"]:
        chat_id = update_data["message"]["chat"]["id"]
        text = update_data["message"]["text"]
        
        if text == "/start":
            response_text = "👋 Привет! Я бот для расчета стоимости бурения скважин."
        elif text == "/help":
            response_text = "📋 Команды бота:\n/start - начать работу\n/help - показать помощь"
        else:
            response_text = f"Вы написали: {text}"
        
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": response_text
        })
    
    return {"ok": True}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Если запрос на настройку вебхука
            if self.path == "/api/simple-webhook" or self.path == "/simple-webhook":
                result = set_webhook()
                
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
            else:
                # Для других GET запросов
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "message": "Simple webhook endpoint is running",
                    "python_version": python_version,
                    "path": self.path
                }).encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка при обработке GET запроса: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e),
                "python_version": python_version
            }).encode('utf-8'))
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update_json = json.loads(post_data.decode('utf-8'))
            
            logger.info(f"Получен POST запрос: {self.path}")
            
            # Обрабатываем обновление от Telegram
            result = process_update(update_json)
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка в обработчике POST: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e),
                "python_version": python_version
            }).encode('utf-8')) 