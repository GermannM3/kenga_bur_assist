from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен")
    BOT_TOKEN = "7559539951:AAG3SL-275Z0-4M24MUrA5p7feNd-SW1py4"  # Используем резервный токен

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Простой обработчик команды /start для тестирования
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "👋 Привет! Я бот для расчета стоимости бурения скважин.\n\n"
        "Пожалуйста, используйте команду /calc для начала расчета."
    )

# Простой обработчик команды /help
async def cmd_help(message: types.Message):
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    await message.answer(
        "📋 Помощь по боту:\n\n"
        "/start - начать работу с ботом\n"
        "/calc - начать расчет стоимости бурения\n"
        "/help - показать эту справку"
    )

# Простой обработчик для тестового сообщения
async def test_message_handler(message: types.Message):
    logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text}")
    await message.answer("Получил ваше сообщение. Для начала работы введите /start")

# Регистрация обработчиков
dp.register_message_handler(cmd_start, commands=["start"])
dp.register_message_handler(cmd_help, commands=["help"])
dp.register_message_handler(test_message_handler)

# Функция для обработки обновлений от Telegram
async def process_update(update_json):
    logger.info("Получено обновление от Telegram")
    logger.info(f"Данные обновления: {json.dumps(update_json)[:200]}...")
    
    # Создаем объект Update из JSON-данных
    update = types.Update(**update_json)
    
    # Обрабатываем обновление через диспетчер
    results = await dp.process_update(update)
    logger.info(f"Результаты обработки: {results}")
    
    return {"ok": True}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update_json = json.loads(post_data.decode('utf-8'))
            
            logger.info(f"Получен POST запрос: {self.path}")
            
            # Обрабатываем обновление от Telegram
            result = asyncio.run(process_update(update_json))
            
            # Отправляем успешный ответ для Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка в обработчике webhook: {e}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e)
            }).encode('utf-8'))
            
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "message": "Telegram webhook endpoint is running", 
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }).encode('utf-8')) 