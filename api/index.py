from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging
from api.telegram import process_update  # Исправленный импорт функции обработки обновлений

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            logger.info(f"Получен GET запрос: {self.path}")
            
            # Базовая информация о системе
            response_data = {
                "status": "ok",
                "message": "Python API работает",
                "path": self.path,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "environment": {
                    "TELEGRAM_BOT_TOKEN": "available" if os.environ.get("TELEGRAM_BOT_TOKEN") else "missing",
                    "BOT_SERVICE_URL": os.environ.get("BOT_SERVICE_URL", "not set"),
                    "VERCEL_URL": os.environ.get("VERCEL_URL", "not set"),
                    "NEXT_PUBLIC_VERCEL_URL": os.environ.get("NEXT_PUBLIC_VERCEL_URL", "not set")
                },
                "headers": dict(self.headers)
            }
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике GET: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e)
            }).encode('utf-8'))
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            logger.info(f"Получен POST запрос: {self.path}")
            logger.info(f"Данные: {json.dumps(data)[:200]}...")  # Логируем только начало данных
            
            # Проверяем, если это обновление от Telegram
            if self.path == '/api/telegram' or self.path == '/telegram':
                logger.info("Обнаружено обновление от Telegram, обрабатываем...")
                
                import asyncio
                # Вызываем асинхронную функцию обработки сообщения
                result = asyncio.run(process_update(data))
                
                # Отправляем успешный ответ для Telegram
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
                return
            
            # Для обычных POST запросов
            response_data = {
                "status": "ok",
                "message": "POST запрос обработан",
                "path": self.path,
                "received_data": data
            }
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике POST: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e)
            }).encode('utf-8'))

