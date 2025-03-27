from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Функция для установки вебхука
async def set_webhook(url):
  try:
      logger.info(f"Setting webhook with URL: {url}")
      
      # Проверяем, что URL начинается с http:// или https://
      if not url.startswith(('http://', 'https://')):
          url = 'https://' + url
          logger.info(f"Added https:// prefix to URL: {url}")
      
      # Формируем полный URL вебхука
      webhook_url = f"{url}/api/telegram"
      logger.info(f"Full webhook URL: {webhook_url}")
      
      # Удаляем текущий вебхук
      logger.info("Deleting current webhook")
      await bot.delete_webhook()
      
      # Устанавливаем новый вебхук
      logger.info("Setting new webhook")
      result = await bot.set_webhook(webhook_url)
      logger.info(f"Webhook set result: {result}")
      
      # Получаем информацию о вебхуке
      webhook_info = await bot.get_webhook_info()
      logger.info(f"New webhook info: {webhook_info}")
      
      return {
          "success": result,
          "webhook_url": webhook_url,
          "webhook_info": webhook_info.to_dict()
      }
  except Exception as e:
      logger.error(f"Error setting webhook: {e}")
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
          logger.error(f"Error in handler: {e}")
          self.send_response(500)
          self.send_header('Content-type', 'application/json')
          self.end_headers()
          self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

