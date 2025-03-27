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
    "Домодедовский район",
    "Дубна",
    "Егорьевский район",
    "Железнодорожный",
    "Жуковский",
    "Зарайский район",
    "Звенигород",
    "Ивантеевка",
    "Истринский район",
    "Каширский район",
    "Климовск",
    "Клинский район",
    "Коломенский район",
    "Королёв",
    "Красногорский район",
    "Ленинский район",
    "Лотошинский район",
    "Луховицкий район",
    "Люберцы",
    "Можайский район",
    "Москва",
    "Наро-Фоминский район",
    "Ногинский район",
    "Одинцовский район",
    "Озёрский район",
    "Пушкинский район",
    "Раменский район",
    "Рублёво",
    "Рузский район",
    "Сергиево-Посадский район",
    "Серебряно-Прудский район",
    "Серпуховский район",
    "Ступинский район",
    "Щёлковский район",
    "Талдомский район",
    "Чеховский район",
    "Шатурский район",
    "Шаховский район",
    "Электросталь",
    "Электроугли"
]

# Глубины для районов (из предоставленных данных)
DISTRICT_DEPTHS = {
    "Александровский район": [[40, 60], [60, 180]],
    "Балашихинский район": [[15, 40], [30, 160]],
    "Бронницы": [[45, 65]],
    "Видное": [[20, 30], [25, 120]],
    "Волоколамский район": [[30, 60], [35, 180]],
    "Воскресенский район": [[35, 100]],
    "Дмитровский район": [[30, 50], [60, 80], [70, 180]],
    "Домодедовский район": [[25, 90]],
    "Дубна": [[25, 50], [70, 110]],
    "Егорьевский район": [[40, 100]],
    "Железнодорожный": [],
    "Жуковский": [[50, 85]],
    "Зарайский район": [[45, 110]],
    "Звенигород": [[15, 30], [45, 120]],
    "Ивантеевка": [[15, 40], [45, 110]],
    "Истринский район": [[15, 40], [55, 80], [60, 180]],
    "Каширский район": [[40, 150]],
    "Климовск": [[45, 75]],
    "Клинский район": [[30, 50], [60, 80], [70, 180]],
    "Коломенский район": [[45, 90]],
    "Королёв": [[45, 70]],
    "Красногорский район": [[60, 120]],
    "Ленинский район": [[20, 30], [25, 120]],
    "Лотошинский район": [[25, 50], [45, 120]],
    "Луховицкий район": [[15, 30], [30, 100]],
    "Люберцы": [[10, 20], [25, 100]],
    "Можайский район": [[25, 50], [45, 130]],
    "Москва": [],
    "Наро-Фоминский район": [[15, 40], [25, 140]],
    "Ногинский район": [[15, 30], [20, 100]],
    "Одинцовский район": [[15, 50], [40, 160]],
    "Озёрский район": [],
    "Пушкинский район": [[15, 60], [45, 120]],
    "Раменский район": [[15, 30], [15, 120]],
    "Рублёво": [[15, 40], [60, 110]],
    "Рузский район": [[15, 40], [20, 180]],
    "Сергиево-Посадский район": [[15, 40], [50, 90], [70, 250]],
    "Серебряно-Прудский район": [[50, 100]],
    "Серпуховский район": [[25, 130]],
    "Ступинский район": [[15, 100]],
    "Щёлковский район": [[10, 30], [15, 90]],
    "Талдомский район": [[15, 50], [60, 130]],
    "Чеховский район": [[30, 60]],
    "Шатурский район": [],
    "Шаховский район": [[15, 40], [50, 130]],
    "Электросталь": [[25, 60]],
    "Электроугли": [[25, 60]]
}

# Наборы оборудования и их компоненты
EQUIPMENT_SETS = {
    "Адаптер №1": {
        "насос": 25000,
        "колонка": 8000
    },
    "Адаптер №2": {
        "насос": 25000,
        "реле": 800,
        "обвязка": 300
    },
    "Адаптер №3": {
        "насос": 25000,
        "гидроаккумулятор": 8000,
        "доведение внутрь объекта": 5000
    },
    "Кессон №1": {
        "кессон": 75000,
        "обратный клапан": 3300,
        "блок автоматики": 5830,
        "трос": 8800,
        "кабель": 16500,
        "зажим троса": 200,
        "фильтр компресс. переход": 350,
        "труба PPR Ø32": 130,
        "труба ПНД Ø32": 10000,
        "запорная арматура, фитинги": 6000,
        "оголовок": 3500
    },
    "Кессон №2": {
        "кессон": 75000,
        "обратный клапан": 3300,
        "блок автоматики": 5830,
        "трос": 8800,
        "кабель": 16500,
        "зажим троса": 200,
        "фильтр компресс. переход": 350,
        "труба PPR Ø32": 130,
        "труба ПНД Ø32": 500,
        "запорная арматура, фитинги": 6000,
        "оголовок": 3500
    },
    "Кессон №3": {
        "кессон": 75000,
        "обратный клапан": 3300,
        "блок автоматики": 5830,
        "трос": 8800,
        "кабель": 16500,
        "зажим троса": 200,
        "фильтр компресс. переход": 350,
        "труба PPR Ø32": 130,
        "труба ПНД Ø32": 500,
        "запорная арматура, фитинги": 6000,
        "оголовок": 3500
    },
    "Станция биологической очистки": {
        "насос для принудительного выброса очищенной воды": 7500,
        "колодец в три кольца с крышкой": 45000
    }
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
    depths = DISTRICT_DEPTHS.get(district, [])
    keyboard = []
    
    if not depths:
        # Если для района нет данных по глубинам, предлагаем стандартные значения
        depths = [[20, 50], [60, 100]]
    
    # Перебираем диапазоны глубин и создаем кнопки
    for depth_range in depths:
        start_depth, end_depth = depth_range
        row = []
        # Добавляем несколько значений из диапазона
        step = max(5, (end_depth - start_depth) // 4)
        for depth in range(start_depth, end_depth + 1, step):
            row.append({"text": f"{depth} м", "callback_data": f"depth_{depth}"})
            if len(row) == 3:  # Максимум 3 кнопки в ряду
                keyboard.append(row)
                row = []
        if row:  # Добавляем оставшиеся кнопки, если есть
            keyboard.append(row)
    
    return {"inline_keyboard": keyboard}

# Функция для создания клавиатуры с наборами оборудования
def create_equipment_sets_keyboard(selected_set=None):
    keyboard = []
    
    for equipment_set in EQUIPMENT_SETS.keys():
        prefix = "✅ " if equipment_set == selected_set else ""
        total_price = sum(EQUIPMENT_SETS[equipment_set].values())
        keyboard.append([{
            "text": f"{prefix}{equipment_set} - {total_price} руб.",
            "callback_data": f"equipment_set_{equipment_set}"
        }])
    
    keyboard.append([{"text": "Индивидуальный набор", "callback_data": "equipment_custom"}])
    keyboard.append([{"text": "Продолжить без оборудования", "callback_data": "equipment_done"}])
    return {"inline_keyboard": keyboard}

# Функция для создания клавиатуры с отдельными компонентами оборудования
def create_equipment_keyboard(selected_equipment=None):
    if selected_equipment is None:
        selected_equipment = []
    
    # Собираем все уникальные компоненты из всех наборов
    all_components = {}
    for equipment_set in EQUIPMENT_SETS.values():
        for component, price in equipment_set.items():
            all_components[component] = price
    
    keyboard = []
    for component, price in all_components.items():
        prefix = "✅ " if component in selected_equipment else ""
        keyboard.append([{
            "text": f"{prefix}{component} - {price} руб.",
            "callback_data": f"equipment_{component}"
        }])
    
    keyboard.append([{"text": "Завершить выбор компонентов", "callback_data": "equipment_done"}])
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
    equipment_cost = sum(EQUIPMENT_SETS.get(item, 0) for item in selected_equipment)
    
    # Стоимость услуг
    services_cost = sum(SERVICES.get(item, 0) for item in selected_services)
    
    return drilling_cost + equipment_cost + services_cost

# Функция создания итогового сообщения с расчетом
def create_final_message(user_data):
    district = user_data.get('district', 'Не выбран')
    depth = user_data.get('depth', 0)
    equipment_set = user_data.get('equipment_set')
    selected_equipment = user_data.get('selected_equipment', [])
    selected_services = user_data.get('selected_services', [])
    
    drilling_cost = calculate_drilling_cost(district, depth)
    
    # Если выбран готовый набор оборудования
    if equipment_set and equipment_set in EQUIPMENT_SETS:
        equipment_items = EQUIPMENT_SETS[equipment_set]
        equipment_cost = sum(equipment_items.values())
    else:
        # Собираем все уникальные компоненты из всех наборов для расчета цены
        all_components = {}
        for equipment_set in EQUIPMENT_SETS.values():
            for component, price in equipment_set.items():
                all_components[component] = price
        
        equipment_cost = sum(all_components.get(item, 0) for item in selected_equipment)
    
    services_cost = sum(SERVICES.get(item, 0) for item in selected_services)
    total_cost = drilling_cost + equipment_cost + services_cost
    
    message = f"📋 *Итоговый расчет стоимости бурения*\n\n"
    message += f"🏡 *Район:* {district}\n"
    message += f"📏 *Глубина:* {depth} м\n\n"
    
    message += f"💰 *Стоимость бурения:* {drilling_cost} руб.\n\n"
    
    if equipment_set and equipment_set in EQUIPMENT_SETS:
        message += f"🔧 *Выбранный набор:* {equipment_set}\n"
        for item, price in EQUIPMENT_SETS[equipment_set].items():
            message += f"• {item} - {price} руб.\n"
        message += f"*Итого за оборудование:* {equipment_cost} руб.\n\n"
    elif selected_equipment:
        # Собираем все уникальные компоненты из всех наборов для вывода
        all_components = {}
        for equipment_set in EQUIPMENT_SETS.values():
            for component, price in equipment_set.items():
                all_components[component] = price
        
        message += f"🔧 *Выбранное оборудование:*\n"
        for item in selected_equipment:
            price = all_components.get(item, 0)
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
            'equipment_set': None,
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
            'equipment_set': None,
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
                   "/help - показать эту справку\n"
                   "/reset - сбросить текущий расчет\n\n"
                   "🔹 *Как пользоваться*:\n\n"
                   "1. Выберите район\n"
                   "2. Укажите глубину бурения\n"
                   "3. Выберите набор оборудования или отдельные компоненты\n"
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
            'equipment_set': None,
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
            'equipment_set': None,
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
                   f"Выберите набор оборудования:",
            "parse_mode": "Markdown",
            "reply_markup": create_equipment_sets_keyboard(user_data.get('equipment_set'))
        })
    
    # Обработка выбора набора оборудования
    elif callback_data.startswith('equipment_set_'):
        equipment_set = callback_data.replace('equipment_set_', '')
        user_data['equipment_set'] = equipment_set
        user_data['selected_equipment'] = list(EQUIPMENT_SETS[equipment_set].keys())
        user_data['state'] = UserState.SERVICES_SELECTION.value
        
        # Рассчитываем стоимость оборудования
        equipment_cost = sum(EQUIPMENT_SETS[equipment_set].values())
        
        telegram_api_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"🔧 Выбран набор: *{equipment_set}*\n\n"
                   f"💰 Стоимость оборудования: *{equipment_cost} руб.*\n\n"
                   f"Теперь выберите дополнительные услуги:",
            "parse_mode": "Markdown",
            "reply_markup": create_services_keyboard(user_data.get('selected_services', []))
        })
    
    # Обработка запроса на индивидуальный набор оборудования
    elif callback_data == 'equipment_custom':
        user_data['equipment_set'] = None
        user_data['selected_equipment'] = []
        
        telegram_api_request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"🔧 Выберите компоненты оборудования по отдельности:",
            "parse_mode": "Markdown",
            "reply_markup": create_equipment_keyboard(user_data.get('selected_equipment', []))
        })
    
    # Обработка выбора компонентов оборудования
    elif callback_data.startswith('equipment_'):
        if callback_data == 'equipment_done':
            user_data['state'] = UserState.SERVICES_SELECTION.value
            
            # Собираем все уникальные компоненты из всех наборов для расчета цены
            all_components = {}
            for equipment_set in EQUIPMENT_SETS.values():
                for component, price in equipment_set.items():
                    all_components[component] = price
            
            # Рассчитываем стоимость выбранного оборудования
            equipment_cost = sum(all_components.get(item, 0) for item in user_data.get('selected_equipment', []))
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "🔧 Выбор оборудования завершен.\n\n"
                       f"💰 Стоимость оборудования: *{equipment_cost} руб.*\n\n"
                       f"Теперь выберите дополнительные услуги:",
                "parse_mode": "Markdown",
                "reply_markup": create_services_keyboard(user_data.get('selected_services', []))
            })
        else:
            component = callback_data.replace('equipment_', '')
            
            # Переключаем выбор компонента (добавляем или удаляем)
            if 'selected_equipment' not in user_data:
                user_data['selected_equipment'] = []
                
            if component in user_data['selected_equipment']:
                user_data['selected_equipment'].remove(component)
            else:
                user_data['selected_equipment'].append(component)
            
            # Собираем все уникальные компоненты из всех наборов для расчета цены
            all_components = {}
            for equipment_set in EQUIPMENT_SETS.values():
                for comp, price in equipment_set.items():
                    all_components[comp] = price
            
            equipment_cost = sum(all_components.get(item, 0) for item in user_data['selected_equipment'])
            
            telegram_api_request("editMessageText", {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🔧 Выберите компоненты оборудования:\n"
                       f"💰 Текущая стоимость оборудования: *{equipment_cost} руб.*\n\n",
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
            
            # Расчет стоимости оборудования
            if user_data.get('equipment_set') and user_data['equipment_set'] in EQUIPMENT_SETS:
                equipment_cost = sum(EQUIPMENT_SETS[user_data['equipment_set']].values())
            else:
                # Собираем все уникальные компоненты
                all_components = {}
                for equipment_set in EQUIPMENT_SETS.values():
                    for component, price in equipment_set.items():
                        all_components[component] = price
                
                equipment_cost = sum(all_components.get(item, 0) for item in user_data.get('selected_equipment', []))
            
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
            'equipment_set': None,
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