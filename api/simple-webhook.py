from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import sys
import platform
import urllib.request
import urllib.parse
import time
from enum import Enum

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

# Состояния FSM (конечного автомата) для пользователя
class UserState(Enum):
    START = 0
    DISTRICT_SELECTION = 1
    DEPTH_SELECTION = 2
    EQUIPMENT_SELECTION = 3
    SERVICES_SELECTION = 4
    FINAL_CALCULATION = 5

# Данные о районах и ценах
# В реальном приложении нужно хранить в JSON или загружать из БД
# Это упрощенная версия данных из lib/drilling-data.ts
DISTRICTS = [
    "Александровский район",
    "Балашихинский район",
    "Бронницы",
    "Видное",
    "Волоколамский район",
    "Воскресенский район",
    "Дмитровский район",
    "Домодедовский район"
]

# Глубины для районов (упрощенный вариант)
DISTRICT_DEPTHS = {
    "Александровский район": [40, 50, 60, 70, 80, 90, 100],
    "Балашихинский район": [15, 20, 25, 30, 35, 40],
    "Бронницы": [45, 50, 55, 60, 65],
    "Видное": [20, 25, 30],
    "Волоколамский район": [30, 35, 40, 45, 50, 55, 60],
    "Воскресенский район": [35, 40, 45, 50, 55, 60],
    "Дмитровский район": [30, 40, 50, 70, 80, 90, 100],
    "Домодедовский район": [25, 30, 35, 40, 45, 50, 60, 70, 80, 90]
}

# Оборудование и цены
EQUIPMENT = {
    "Скважинный насос Belamos tf 80-110": 25000,
    "Насос Grundfos SQ 3-65": 45000,
    "Кессон пластиковый": 35000,
    "Гидроаккумулятор 50 л": 6000,
    "Оголовок скважины": 3500,
    "Фильтр грубой очистки": 3000
}

# Услуги и цены
SERVICES = {
    "Монтаж кессона": 19000,
    "Монтаж систем автоматики": 2000,
    "Транспортные расходы": 3000,
    "Анализ воды": 5000,
    "Монтаж гидроаккумулятора": 2900
}

# Хранилище состояний пользователей в памяти
# В реальном приложении нужно использовать Redis или другую БД
user_states = {}

# Базовая стоимость бурения за метр
BASE_DRILLING_COST = 2900

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

# Функция для создания клавиатуры с районами
def create_districts_keyboard():
    keyboard = []
    row = []
    
    for i, district in enumerate(DISTRICTS, 1):
        row.append({"text": district, "callback_data": f"district_{district}"})
        
        # По 2 кнопки в ряду
        if i % 2 == 0 or i == len(DISTRICTS):
            keyboard.append(row)
            row = []
    
    return {"inline_keyboard": keyboard}

# Функция для создания клавиатуры с глубинами
def create_depths_keyboard(district):
    depths = DISTRICT_DEPTHS.get(district, [30, 40, 50])
    keyboard = []
    row = []
    
    for i, depth in enumerate(depths, 1):
        row.append({"text": f"{depth} м", "callback_data": f"depth_{depth}"})
        
        # По 3 кнопки в ряду
        if i % 3 == 0 or i == len(depths):
            keyboard.append(row)
            row = []
    
    return {"inline_keyboard": keyboard}

# Функция для создания клавиатуры с оборудованием
def create_equipment_keyboard(selected_equipment=None):
    if selected_equipment is None:
        selected_equipment = []
    
    keyboard = []
    for equip, price in EQUIPMENT.items():
        prefix = "✅ " if equip in selected_equipment else ""
        keyboard.append([{
            "text": f"{prefix}{equip} - {price} руб.",
            "callback_data": f"equipment_{equip}"
        }])
    
    keyboard.append([{"text": "Завершить выбор оборудования", "callback_data": "equipment_done"}])
    return {"inline_keyboard": keyboard}

# Функция для создания клавиатуры с услугами
def create_services_keyboard(selected_services=None):
    if selected_services is None:
        selected_services = []
    
    keyboard = []
    for service, price in SERVICES.items():
        prefix = "✅ " if service in selected_services else ""
        keyboard.append([{
            "text": f"{prefix}{service} - {price} руб.",
            "callback_data": f"service_{service}"
        }])
    
    keyboard.append([{"text": "Завершить выбор услуг", "callback_data": "services_done"}])
    return {"inline_keyboard": keyboard}

# Функция расчета стоимости бурения
def calculate_drilling_cost(district, depth):
    return depth * BASE_DRILLING_COST

# Функция расчета общей стоимости
def calculate_total_cost(district, depth, selected_equipment, selected_services):
    # Стоимость бурения
    drilling_cost = calculate_drilling_cost(district, depth)
    
    # Стоимость оборудования
    equipment_cost = sum(EQUIPMENT.get(item, 0) for item in selected_equipment)
    
    # Стоимость услуг
    services_cost = sum(SERVICES.get(item, 0) for item in selected_services)
    
    return drilling_cost + equipment_cost + services_cost

# Функция создания итогового сообщения с расчетом
def create_final_message(user_data):
    district = user_data.get('district', 'Не выбран')
    depth = user_data.get('depth', 0)
    selected_equipment = user_data.get('selected_equipment', [])
    selected_services = user_data.get('selected_services', [])
    
    drilling_cost = calculate_drilling_cost(district, depth)
    equipment_cost = sum(EQUIPMENT.get(item, 0) for item in selected_equipment)
    services_cost = sum(SERVICES.get(item, 0) for item in selected_services)
    total_cost = drilling_cost + equipment_cost + services_cost
    
    message = f"📋 *Итоговый расчет стоимости бурения*\n\n"
    message += f"🏡 *Район:* {district}\n"
    message += f"📏 *Глубина:* {depth} м\n\n"
    
    message += f"💰 *Стоимость бурения:* {drilling_cost} руб.\n\n"
    
    if selected_equipment:
        message += f"🔧 *Выбранное оборудование:*\n"
        for item in selected_equipment:
            price = EQUIPMENT.get(item, 0)
            message += f"• {item} - {price} руб.\n"
        message += f"*Итого за оборудование:* {equipment_cost} руб.\n\n"
    
    if selected_services:
        message += f"🛠 *Выбранные услуги:*\n"
        for item in selected_services:
            price = SERVICES.get(item, 0)
            message += f"• {item} - {price} руб.\n"
        message += f"*Итого за услуги:* {services_cost} руб.\n\n"
    
    message += f"*ОБЩАЯ СТОИМОСТЬ: {total_cost} руб.*"
    
    return message

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
    logger.info(f"Получено обновление от Telegram")
    
    # Обработка callback-запросов (нажатий на кнопки)
    if 'callback_query' in update_data:
        return process_callback_query(update_data['callback_query'])
    
    # Обработка текстовых сообщений
    elif 'message' in update_data and 'text' in update_data['message']:
        return process_message(update_data['message'])
    
    return {"ok": True}

# Обработка текстовых сообщений
def process_message(message):
    chat_id = message['chat']['id']
    text = message['text']
    user_id = str(message['from']['id'])
    
    # Инициализация состояния пользователя если его нет
    if user_id not in user_states:
        user_states[user_id] = {
            'state': UserState.START.value,
            'district': None,
            'depth': None,
            'selected_equipment': [],
            'selected_services': [],
            'timestamp': time.time()
        }
    
    # Обработка команд
    if text == '/start':
        # Сбрасываем состояние пользователя
        user_states[user_id] = {
            'state': UserState.DISTRICT_SELECTION.value,
            'district': None,
            'depth': None,
            'selected_equipment': [],
            'selected_services': [],
            'timestamp': time.time()
        }
        
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": "👋 Добро пожаловать в калькулятор стоимости бурения скважин!\n\nВыберите район, в котором планируется бурение:",
            "reply_markup": create_districts_keyboard()
        })
    
    elif text == '/help':
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": "🔹 *Команды бота*:\n\n"
                   "/start - начать расчет стоимости бурения\n"
                   "/help - показать эту справку\n\n"
                   "🔹 *Как пользоваться*:\n\n"
                   "1. Выберите район\n"
                   "2. Укажите глубину бурения\n"
                   "3. Выберите необходимое оборудование\n"
                   "4. Выберите дополнительные услуги\n"
                   "5. Получите итоговый расчет стоимости\n\n"
                   "Для начала работы отправьте команду /start",
            "parse_mode": "Markdown"
        })
    
    elif text == '/reset':
        # Сбрасываем состояние пользователя
        user_states[user_id] = {
            'state': UserState.START.value,
            'district': None,
            'depth': None,
            'selected_equipment': [],
            'selected_services': [],
            'timestamp': time.time()
        }
        
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": "🔄 Все данные сброшены. Отправьте /start чтобы начать новый расчет."
        })
    
    else:
        # Если это не команда, отправляем инструкцию
        telegram_api_request("sendMessage", {
            "chat_id": chat_id,
            "text": "Отправьте /start чтобы начать расчет стоимости бурения или /help для справки."
        })
    
    return {"ok": True}

# Обработка нажатий на кнопки
def process_callback_query(callback_query):
    user_id = str(callback_query['from']['id'])
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    callback_data = callback_query['data']
    
    # Инициализация состояния пользователя если его нет
    if user_id not in user_states:
        user_states[user_id] = {
            'state': UserState.START.value,
            'district': None,
            'depth': None,
            'selected_equipment': [],
            'selected_services': [],
            'timestamp': time.time()
        }
    
    user_data = user_states[user_id]
    
    # Отправляем ответ на callback query чтобы убрать "часики" на кнопке
    telegram_api_request("answerCallbackQuery", {
        "callback_query_id": callback_query['id']
    })
    
    # Обработка выбора района
    if callback_data.startswith('district_'):
        district = callback_data.replace('district_', '')
        user_data['district'] = district
        user_data['state'] = UserState.DEPTH_SELECTION.value
        
        telegram_api_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"🏡 Выбран район: *{district}*\n\nТеперь выберите глубину бурения:",
            "parse_mode": "Markdown",
            "reply_markup": create_depths_keyboard(district)
        })
    
    # Обработка выбора глубины
    elif callback_data.startswith('depth_'):
        depth = int(callback_data.replace('depth_', ''))
        user_data['depth'] = depth
        user_data['state'] = UserState.EQUIPMENT_SELECTION.value
        
        # Рассчитываем стоимость бурения
        drilling_cost = calculate_drilling_cost(user_data['district'], depth)
        
        telegram_api_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"📏 Выбрана глубина: *{depth} м*\n\n"
                   f"💰 Стоимость бурения: *{drilling_cost} руб.*\n\n"
                   f"Выберите необходимое оборудование:",
            "parse_mode": "Markdown",
            "reply_markup": create_equipment_keyboard(user_data.get('selected_equipment', []))
        })
    
    # Обработка выбора оборудования
    elif callback_data.startswith('equipment_'):
        if callback_data == 'equipment_done':
            user_data['state'] = UserState.SERVICES_SELECTION.value
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "🔧 Выбор оборудования завершен.\n\nТеперь выберите дополнительные услуги:",
                "reply_markup": create_services_keyboard(user_data.get('selected_services', []))
            })
        else:
            equipment_item = callback_data.replace('equipment_', '')
            
            # Переключаем выбор оборудования (добавляем или удаляем)
            if 'selected_equipment' not in user_data:
                user_data['selected_equipment'] = []
                
            if equipment_item in user_data['selected_equipment']:
                user_data['selected_equipment'].remove(equipment_item)
            else:
                user_data['selected_equipment'].append(equipment_item)
            
            drilling_cost = calculate_drilling_cost(user_data['district'], user_data['depth'])
            equipment_cost = sum(EQUIPMENT.get(item, 0) for item in user_data['selected_equipment'])
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"📏 Глубина: *{user_data['depth']} м*\n"
                       f"💰 Стоимость бурения: *{drilling_cost} руб.*\n"
                       f"🔧 Стоимость оборудования: *{equipment_cost} руб.*\n\n"
                       f"Выберите необходимое оборудование:",
                "parse_mode": "Markdown",
                "reply_markup": create_equipment_keyboard(user_data['selected_equipment'])
            })
    
    # Обработка выбора услуг
    elif callback_data.startswith('service_'):
        if callback_data == 'services_done':
            user_data['state'] = UserState.FINAL_CALCULATION.value
            
            # Создаем итоговое сообщение
            final_message = create_final_message(user_data)
            
            # Предлагаем клавиатуру для новых расчетов
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔄 Сделать новый расчет", "callback_data": "new_calculation"}]
                ]
            }
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": final_message,
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            })
        else:
            service_item = callback_data.replace('service_', '')
            
            # Переключаем выбор услуги (добавляем или удаляем)
            if 'selected_services' not in user_data:
                user_data['selected_services'] = []
                
            if service_item in user_data['selected_services']:
                user_data['selected_services'].remove(service_item)
            else:
                user_data['selected_services'].append(service_item)
            
            drilling_cost = calculate_drilling_cost(user_data['district'], user_data['depth'])
            equipment_cost = sum(EQUIPMENT.get(item, 0) for item in user_data['selected_equipment'])
            services_cost = sum(SERVICES.get(item, 0) for item in user_data['selected_services'])
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"📏 Глубина: *{user_data['depth']} м*\n"
                       f"💰 Стоимость бурения: *{drilling_cost} руб.*\n"
                       f"🔧 Стоимость оборудования: *{equipment_cost} руб.*\n"
                       f"🛠 Стоимость услуг: *{services_cost} руб.*\n\n"
                       f"Выберите дополнительные услуги:",
                "parse_mode": "Markdown",
                "reply_markup": create_services_keyboard(user_data['selected_services'])
            })
    
    # Обработка запроса на новый расчет
    elif callback_data == 'new_calculation':
        # Сбрасываем состояние пользователя
        user_states[user_id] = {
            'state': UserState.DISTRICT_SELECTION.value,
            'district': None,
            'depth': None,
            'selected_equipment': [],
            'selected_services': [],
            'timestamp': time.time()
        }
        
        telegram_api_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": "👋 Начинаем новый расчет стоимости бурения скважины!\n\nВыберите район, в котором планируется бурение:",
            "reply_markup": create_districts_keyboard()
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