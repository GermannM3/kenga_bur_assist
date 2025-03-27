from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не задан")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Данные о районах и глубинах
districts = [
    "Александровский район",
    "Балашихинский район",
    "Бронницы",
    "Видное",
    "Волоколамский район",
]

# Глубины по районам (упрощенно)
district_depths = {
    "Александровский район": [40, 50, 60, 70, 80, 90, 100],
    "Балашихинский район": [15, 20, 25, 30, 35, 40],
    "Бронницы": [45, 50, 55, 60, 65],
    "Видное": [20, 25, 30],
    "Волоколамский район": [30, 35, 40, 45, 50, 55, 60],
}

# Оборудование и цены
equipment = {
    "Скважинный насос Belamos tf 80-110": 25000,
    "Насос Grundfos SQ 3-65": 45000,
    "Кессон пластиковый": 35000,
    "Гидроаккумулятор 50 л": 6000,
}

# Услуги и цены
services = {
    "Монтаж кессона": 19000,
    "Монтаж систем автоматики": 2000,
    "Транспортные расходы": 3000,
    "Анализ воды": 5000,
}

# Хранилище состояний пользователей
user_states = {}

# Функция для обработки обновлений от Telegram
async def process_update(update_data):
    # Создаем объект Update из данных
    update = Update.de_json(update_data, bot)
    
    # Обрабатываем команды
    if update.message and update.message.text:
        if update.message.text == '/start':
            await start_command(update)
            return
        elif update.message.text == '/reset':
            await reset_command(update)
            return
        else:
            # Для всех остальных сообщений отправляем инструкцию
            await update.message.reply_text("Пожалуйста, используйте команду /start для начала работы с ботом или /reset для сброса.")
            return
    
    # Обрабатываем нажатия на кнопки
    if update.callback_query:
        callback_data = update.callback_query.data
        
        if callback_data.startswith('district_'):
            await process_district_selection(update)
        elif callback_data.startswith('depth_'):
            await process_depth_selection(update)
        elif callback_data.startswith('equipment_') and callback_data != 'equipment_done':
            await process_equipment_selection(update)
        elif callback_data == 'equipment_done':
            await process_equipment_done(update)
        elif callback_data.startswith('service_'):
            await process_service_selection(update)
        elif callback_data == 'services_done':
            await process_services_done(update)
        elif callback_data == 'start_over':
            await process_start_over(update)

# Обработчик команды /start
async def start_command(update):
    user_id = update.effective_user.id
    logger.info(f"Получена команда /start от пользователя {user_id}")
    
    # Инициализация состояния пользователя
    user_states[user_id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = []
    for i in range(0, len(districts), 2):
        row = []
        for j in range(2):
            if i + j < len(districts):
                row.append({
                    "text": districts[i + j],
                    "callback_data": f"district_{districts[i + j]}"
                })
        keyboard.append(row)
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await update.message.reply_text(
        "Добро пожаловать в калькулятор стоимости бурения! Выберите район:",
        reply_markup=reply_markup
    )

# Обработчик команды /reset
async def reset_command(update):
    user_id = update.effective_user.id
    logger.info(f"Получена команда /reset от пользователя {user_id}")
    
    # Сбрасываем состояние пользователя
    user_states[user_id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = []
    for i in range(0, len(districts), 2):
        row = []
        for j in range(2):
            if i + j < len(districts):
                row.append({
                    "text": districts[i + j],
                    "callback_data": f"district_{districts[i + j]}"
                })
        keyboard.append(row)
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await update.message.reply_text(
        "Начинаем заново. Выберите район:",
        reply_markup=reply_markup
    )

# Обработчик выбора района
async def process_district_selection(update):
    query = update.callback_query
    await query.answer()
    
    district = query.data.replace('district_', '')
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} выбрал район: {district}")
    
    # Обновляем состояние пользователя
    if user_id not in user_states:
        user_states[user_id] = {"stage": "initial", "selected_equipment": [], "selected_services": []}
    
    user_states[user_id]["district"] = district
    user_states[user_id]["stage"] = "district_selected"
    
    # Получаем глубины для выбранного района
    depths = district_depths.get(district, [30, 40, 50, 60, 70])
    
    # Создаем клавиатуру с глубинами
    keyboard = []
    for i in range(0, len(depths), 3):
        row = []
        for j in range(3):
            if i + j < len(depths):
                row.append({
                    "text": f"{depths[i + j]} м",
                    "callback_data": f"depth_{depths[i + j]}"
                })
        keyboard.append(row)
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await query.edit_message_text(
        f"Вы выбрали район: {district}. Теперь выберите глубину бурения:",
        reply_markup=reply_markup
    )

# Обработчик выбора глубины
async def process_depth_selection(update):
    query = update.callback_query
    await query.answer()
    
    depth = int(query.data.replace('depth_', ''))
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} выбрал глубину: {depth}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states or "district" not in user_states[user_id]:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    user_states[user_id]["depth"] = depth
    user_states[user_id]["stage"] = "depth_selected"
    
    # Рассчитываем стоимость бурения (упрощенно)
    drilling_cost = depth * 2900  # Базовая стоимость 2900 руб/м
    
    # Создаем клавиатуру с оборудованием
    keyboard = []
    for item in equipment:
        keyboard.append([{
            "text": item,
            "callback_data": f"equipment_{item}"
        }])
    
    keyboard.append([{
        "text": "Завершить выбор оборудования",
        "callback_data": "equipment_done"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await query.edit_message_text(
        f"Вы выбрали глубину: {depth} м\n\nСтоимость бурения: {drilling_cost:,} руб.\n\nВыберите необходимое оборудование:",
        reply_markup=reply_markup
    )

# Обработчик выбора оборудования
async def process_equipment_selection(update):
    query = update.callback_query
    await query.answer()
    
    equipment_item = query.data.replace('equipment_', '')
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} выбрал оборудование: {equipment_item}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Добавляем или удаляем оборудование из списка выбранного
    if equipment_item in user_states[user_id].get("selected_equipment", []):
        user_states[user_id]["selected_equipment"].remove(equipment_item)
    else:
        if "selected_equipment" not in user_states[user_id]:
            user_states[user_id]["selected_equipment"] = []
        user_states[user_id]["selected_equipment"].append(equipment_item)
    
    user_states[user_id]["stage"] = "equipment_selection"
    
    # Создаем клавиатуру с отметками выбранного оборудования
    keyboard = []
    for item in equipment:
        text = f"✅ {item}" if item in user_states[user_id].get("selected_equipment", []) else item
        keyboard.append([{
            "text": text,
            "callback_data": f"equipment_{item}"
        }])
    
    keyboard.append([{
        "text": "Завершить выбор оборудования",
        "callback_data": "equipment_done"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    # Формируем текст сообщения
    message_text = "Выбранное оборудование:\n"
    if user_states[user_id].get("selected_equipment", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_equipment"]])
    else:
        message_text += "Ничего не выбрано"
    
    await query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )

# Обработчик завершения выбора оборудования
async def process_equipment_done(update):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} завершил выбор оборудования")
    
    # Проверяем состояние пользователя
    if user_id not in user_states:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Создаем клавиатуру с услугами
    keyboard = []
    for item in services:
        keyboard.append([{
            "text": item,
            "callback_data": f"service_{item}"
        }])
    
    keyboard.append([{
        "text": "Завершить выбор услуг",
        "callback_data": "services_done"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    # Формируем текст сообщения
    message_text = "Выбранное оборудование:\n"
    if user_states[user_id].get("selected_equipment", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_equipment"]])
    else:
        message_text += "Ничего не выбрано"
    
    message_text += "\n\nВыберите дополнительные услуги:"
    
    await query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )
    
    user_states[user_id]["stage"] = "services_selection"

# Обработчик выбора услуг
async def process_service_selection(update):
    query = update.callback_query
    await query.answer()
    
    service_item = query.data.replace('service_', '')
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} выбрал услугу: {service_item}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Добавляем или удаляем услугу из списка выбранных
    if service_item in user_states[user_id].get("selected_services", []):
        user_states[user_id]["selected_services"].remove(service_item)
    else:
        if "selected_services" not in user_states[user_id]:
            user_states[user_id]["selected_services"] = []
        user_states[user_id]["selected_services"].append(service_item)
    
    # Создаем клавиатуру с отметками выбранных услуг
    keyboard = []
    for item in services:
        text = f"✅ {item}" if item in user_states[user_id].get("selected_services", []) else item
        keyboard.append([{
            "text": text,
            "callback_data": f"service_{item}"
        }])
    
    keyboard.append([{
        "text": "Завершить выбор услуг",
        "callback_data": "services_done"
    }])
    
    reply_markup = {"inline_keyboard": keyboard}
    
    # Формируем текст сообщения
    message_text = "Выбранное оборудование:\n"
    if user_states[user_id].get("selected_equipment", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_equipment"]])
    else:
        message_text += "Ничего не выбрано"
    
    message_text += "\n\nВыбранные услуги:\n"
    if user_states[user_id].get("selected_services", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_services"]])
    else:
        message_text += "Ничего не выбрано"
    
    await query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )

# Обработчик завершения выбора услуг
async def process_services_done(update):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} завершил выбор услуг")
    
    # Проверяем состояние пользователя
    if user_id not in user_states or "district" not in user_states[user_id] or "depth" not in user_states[user_id]:
        await query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Рассчитываем стоимость
    district = user_states[user_id]["district"]
    depth = user_states[user_id]["depth"]
    selected_equipment = user_states[user_id].get("selected_equipment", [])
    selected_services = user_states[user_id].get("selected_services", [])
    
    # Базовая стоимость бурения
    drilling_cost = depth * 2900  # Базовая стоимость 2900 руб/м
    
    # Стоимость оборудования
    equipment_cost = sum(equipment.get(item, 0) for item in selected_equipment)
    
    # Стоимость услуг
    services_cost = sum(services.get(item, 0) for item in selected_services)
    
    # Общая стоимость
    total_cost = drilling_cost + equipment_cost + services_cost
    
    # Формируем сообщение с результатами
    message = f"📋 *Итоговый расчет*\n\n"
    message += f"🏙️ Район: *{district}*\n"
    message += f"🔍 Глубина бурения: *{depth} м*\n\n"
    message += f"💧 Стоимость бурения: *{drilling_cost:,} руб.*\n\n"
    
    message += f"🛠️ Выбранное оборудование:\n"
    if selected_equipment:
        for item in selected_equipment:
            price = equipment.get(item, 0)
            message += f"- {item}: {price:,} руб.\n"
    else:
        message += f"Не выбрано\n"
    
    message += f"\n🔧 Выбранные услуги:\n"
    if selected_services:
        for item in selected_services:
            price = services.get(item, 0)
            message += f"- {item}: {price:,} руб.\n"
    else:
        message += f"Не выбрано\n"
    
    message += f"\n💰 *Итоговая стоимость: {total_cost:,} руб.*"
    
    # Клавиатура для начала заново
    keyboard = [[{
        "text": "Начать заново",
        "callback_data": "start_over"
    }]]
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    user_states[user_id]["stage"] = "final"

# Обработчик кнопки "Начать заново"
async def process_start_over(update):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} начинает заново")
    
    # Сбрасываем состояние пользователя
    user_states[user_id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = []
    for i in range(0, len(districts), 2):
        row = []
        for j in range(2):
            if i + j < len(districts):
                row.append({
                    "text": districts[i + j],
                    "callback_data": f"district_{districts[i + j]}"
                })
        keyboard.append(row)
    
    reply_markup = {"inline_keyboard": keyboard}
    
    await query.edit_message_text(
        "Начинаем заново. Выберите район:",
        reply_markup=reply_markup
    )

# Функция для установки вебхука
async def set_webhook(url):
    webhook_url = f"{url}/api/telegram"
    
    # Удаляем текущий вебхук
    await bot.delete_webhook()
    
    # Устанавливаем новый вебхук
    result = await bot.set_webhook(webhook_url)
    
    # Получаем информацию о вебхуке
    webhook_info = await bot.get_webhook_info()
    
    return {
        "success": result,
        "webhook_url": webhook_url,
        "webhook_info": webhook_info.to_dict()
    }

# Функция для получения информации о вебхуке
async def get_webhook_info():
    webhook_info = await bot.get_webhook_info()
    me = await bot.get_me()
    return {
        "status": "ok",
        "bot_info": me.to_dict(),
        "webhook_info": webhook_info.to_dict()
    }

# Функция для отправки тестового сообщения
async def send_test_message(chat_id):
    message = await bot.send_message(
        chat_id=chat_id,
        text="Тестовое сообщение от бота. Если вы видите это сообщение, значит бот работает корректно!"
    )
    return {
        "success": True,
        "message_info": message.to_dict()
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Парсим JSON-данные
            update_data = json.loads(post_data.decode('utf-8'))
            logger.info(f"Получен вебхук: {json.dumps(update_data)}")
            
            # Обрабатываем обновление
            asyncio.run(process_update(update_data))
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка при обработке вебхука: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode('utf-8'))
    
    def do_GET(self):
        # Для проверки работоспособности вебхука
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Telegram webhook is running"}).encode('utf-8'))

