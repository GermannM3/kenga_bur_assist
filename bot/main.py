import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан")

# Настройки для webhook
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://example.com")  # Будет заменено на реальный хост
WEBHOOK_PATH = "/api/telegram-webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Инициализация FastAPI
app = FastAPI()

# Данные о районах и глубинах
districts = [
    "Александровский район",
    "Балашихинский район",
    "Бронницы",
    # ... остальные районы
]

# Словарь для хранения состояния пользователей
user_states = {}

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    
    # Инициализация состояния пользователя
    user_states[message.from_user.id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in districts:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"district_{district}"))
    
    await message.answer("Добро пожаловать в калькулятор стоимости бурения! Выберите район:", reply_markup=keyboard)

# Обработчик команды /reset
@dp.message_handler(commands=['reset'])
async def cmd_reset(message: types.Message):
    logger.info(f"Получена команда /reset от пользователя {message.from_user.id}")
    
    # Сбрасываем состояние пользователя
    user_states[message.from_user.id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in districts:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"district_{district}"))
    
    await message.answer("Начинаем заново. Выберите район:", reply_markup=keyboard)

# Обработчик выбора района
@dp.callback_query_handler(lambda c: c.data.startswith('district_'))
async def process_district_selection(callback_query: types.CallbackQuery):
    district = callback_query.data.replace('district_', '')
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} выбрал район: {district}")
    
    # Обновляем состояние пользователя
    if user_id not in user_states:
        user_states[user_id] = {"stage": "initial", "selected_equipment": [], "selected_services": []}
    
    user_states[user_id]["district"] = district
    user_states[user_id]["stage"] = "district_selected"
    
    # Здесь должна быть логика получения глубин для выбранного района
    # Для примера используем фиксированные значения
    depths = [30, 40, 50, 60, 70, 80]
    
    # Создаем клавиатуру с глубинами
    keyboard = InlineKeyboardMarkup(row_width=3)
    for depth in depths:
        keyboard.add(InlineKeyboardButton(f"{depth} м", callback_data=f"depth_{depth}"))
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Вы выбрали район: {district}. Теперь выберите глубину бурения:",
        reply_markup=keyboard
    )
    
    # Отвечаем на callback_query, чтобы убрать часы загрузки
    await callback_query.answer()

# Обработчик выбора глубины
@dp.callback_query_handler(lambda c: c.data.startswith('depth_'))
async def process_depth_selection(callback_query: types.CallbackQuery):
    depth = int(callback_query.data.replace('depth_', ''))
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} выбрал глубину: {depth}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states or "district" not in user_states[user_id]:
        await callback_query.answer("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    user_states[user_id]["depth"] = depth
    user_states[user_id]["stage"] = "depth_selected"
    
    # Рассчитываем стоимость бурения (упрощенно)
    drilling_cost = depth * 2900  # Базовая стоимость 2900 руб/м
    
    # Здесь должна быть логика получения списка оборудования
    # Для примера используем фиксированные значения
    equipment_list = [
        "Скважинный насос Belamos tf 80-110",
        "Насос Grundfos SQ 3-65",
        "Кессон пластиковый",
        "Гидроаккумулятор 50 л"
    ]
    
    # Создаем клавиатуру с оборудованием
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item in equipment_list:
        keyboard.add(InlineKeyboardButton(item, callback_data=f"equipment_{item}"))
    
    keyboard.add(InlineKeyboardButton("Завершить выбор оборудования", callback_data="equipment_done"))
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Вы выбрали глубину: {depth} м\n\nСтоимость бурения: {drilling_cost} руб.\n\nВыберите необходимое оборудование:",
        reply_markup=keyboard
    )
    
    await callback_query.answer()

# Обработчик выбора оборудования
@dp.callback_query_handler(lambda c: c.data.startswith('equipment_') and not c.data == 'equipment_done')
async def process_equipment_selection(callback_query: types.CallbackQuery):
    equipment = callback_query.data.replace('equipment_', '')
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} выбрал оборудование: {equipment}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states:
        await callback_query.answer("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Добавляем или удаляем оборудование из списка выбранного
    if equipment in user_states[user_id].get("selected_equipment", []):
        user_states[user_id]["selected_equipment"].remove(equipment)
    else:
        if "selected_equipment" not in user_states[user_id]:
            user_states[user_id]["selected_equipment"] = []
        user_states[user_id]["selected_equipment"].append(equipment)
    
    user_states[user_id]["stage"] = "equipment_selection"
    
    # Получаем список всего оборудования
    equipment_list = [
        "Скважинный насос Belamos tf 80-110",
        "Насос Grundfos SQ 3-65",
        "Кессон пластиковый",
        "Гидроаккумулятор 50 л"
    ]
    
    # Создаем клавиатуру с отметками выбранного оборудования
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item in equipment_list:
        text = f"✅ {item}" if item in user_states[user_id].get("selected_equipment", []) else item
        keyboard.add(InlineKeyboardButton(text, callback_data=f"equipment_{item}"))
    
    keyboard.add(InlineKeyboardButton("Завершить выбор оборудования", callback_data="equipment_done"))
    
    # Формируем текст сообщения
    message_text = "Выбранное оборудование:\n"
    if user_states[user_id].get("selected_equipment", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_equipment"]])
    else:
        message_text += "Ничего не выбрано"
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        reply_markup=keyboard
    )
    
    await callback_query.answer()

# Обработчик завершения выбора оборудования
@dp.callback_query_handler(lambda c: c.data == 'equipment_done')
async def process_equipment_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} завершил выбор оборудования")
    
    # Проверяем состояние пользователя
    if user_id not in user_states:
        await callback_query.answer("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Здесь должна быть логика получения списка услуг
    # Для примера используем фиксированные значения
    services_list = [
        "Монтаж кессона",
        "Монтаж систем автоматики",
        "Транспортные расходы",
        "Анализ воды"
    ]
    
    # Создаем клавиатуру с услугами
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item in services_list:
        keyboard.add(InlineKeyboardButton(item, callback_data=f"service_{item}"))
    
    keyboard.add(InlineKeyboardButton("Завершить выбор услуг", callback_data="services_done"))
    
    # Формируем текст сообщения
    message_text = "Выбранное оборудование:\n"
    if user_states[user_id].get("selected_equipment", []):
        message_text += "\n".join([f"- {item}" for item in user_states[user_id]["selected_equipment"]])
    else:
        message_text += "Ничего не выбрано"
    
    message_text += "\n\nВыберите дополнительные услуги:"
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        reply_markup=keyboard
    )
    
    user_states[user_id]["stage"] = "services_selection"
    await callback_query.answer()

# Обработчик выбора услуг
@dp.callback_query_handler(lambda c: c.data.startswith('service_'))
async def process_service_selection(callback_query: types.CallbackQuery):
    service = callback_query.data.replace('service_', '')
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} выбрал услугу: {service}")
    
    # Проверяем и обновляем состояние пользователя
    if user_id not in user_states:
        await callback_query.answer("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Добавляем или удаляем услугу из списка выбранных
    if service in user_states[user_id].get("selected_services", []):
        user_states[user_id]["selected_services"].remove(service)
    else:
        if "selected_services" not in user_states[user_id]:
            user_states[user_id]["selected_services"] = []
        user_states[user_id]["selected_services"].append(service)
    
    # Получаем список всех услуг
    services_list = [
        "Монтаж кессона",
        "Монтаж систем автоматики",
        "Транспортные расходы",
        "Анализ воды"
    ]
    
    # Создаем клавиатуру с отметками выбранных услуг
    keyboard = InlineKeyboardMarkup(row_width=1)
    for item in services_list:
        text = f"✅ {item}" if item in user_states[user_id].get("selected_services", []) else item
        keyboard.add(InlineKeyboardButton(text, callback_data=f"service_{item}"))
    
    keyboard.add(InlineKeyboardButton("Завершить выбор услуг", callback_data="services_done"))
    
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
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        reply_markup=keyboard
    )
    
    await callback_query.answer()

# Обработчик завершения выбора услуг
@dp.callback_query_handler(lambda c: c.data == 'services_done')
async def process_services_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} завершил выбор услуг")
    
    # Проверяем состояние пользователя
    if user_id not in user_states or "district" not in user_states[user_id] or "depth" not in user_states[user_id]:
        await callback_query.answer("Произошла ошибка. Пожалуйста, начните заново с команды /start")
        return
    
    # Рассчитываем стоимость (упрощенно)
    district = user_states[user_id]["district"]
    depth = user_states[user_id]["depth"]
    selected_equipment = user_states[user_id].get("selected_equipment", [])
    selected_services = user_states[user_id].get("selected_services", [])
    
    # Базовая стоимость бурения
    drilling_cost = depth * 2900  # Базовая стоимость 2900 руб/м
    
    # Стоимость оборудования (упрощенно)
    equipment_prices = {
        "Скважинный насос Belamos tf 80-110": 25000,
        "Насос Grundfos SQ 3-65": 45000,
        "Кессон пластиковый": 35000,
        "Гидроаккумулятор 50 л": 6000
    }
    
    equipment_cost = sum(equipment_prices.get(item, 0) for item in selected_equipment)
    
    # Стоимость услуг (упрощенно)
    service_prices = {
        "Монтаж кессона": 19000,
        "Монтаж систем автоматики": 2000,
        "Транспортные расходы": 3000,
        "Анализ воды": 5000
    }
    
    services_cost = sum(service_prices.get(item, 0) for item in selected_services)
    
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
            price = equipment_prices.get(item, 0)
            message += f"- {item}: {price:,} руб.\n"
    else:
        message += f"Не выбрано\n"
    
    message += f"\n🔧 Выбранные услуги:\n"
    if selected_services:
        for item in selected_services:
            price = service_prices.get(item, 0)
            message += f"- {item}: {price:,} руб.\n"
    else:
        message += f"Не выбрано\n"
    
    message += f"\n💰 *Итоговая стоимость: {total_cost:,} руб.*"
    
    # Клавиатура для начала заново
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Начать заново", callback_data="start_over"))
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    user_states[user_id]["stage"] = "final"
    await callback_query.answer()

# Обработчик кнопки "Начать заново"
@dp.callback_query_handler(lambda c: c.data == 'start_over')
async def process_start_over(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    logger.info(f"Пользователь {user_id} начинает заново")
    
    # Сбрасываем состояние пользователя
    user_states[user_id] = {
        "stage": "initial",
        "selected_equipment": [],
        "selected_services": []
    }
    
    # Создаем клавиатуру с районами
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in districts:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"district_{district}"))
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Начинаем заново. Выберите район:",
        reply_markup=keyboard
    )
    
    await callback_query.answer()

# Обработчик для всех остальных сообщений
@dp.message_handler()
async def echo(message: types.Message):
    logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text}")
    await message.answer("Пожалуйста, используйте команду /start для начала работы с ботом или /reset для сброса.")

# FastAPI эндпоинт для вебхука
@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {json.dumps(data)}")
        
        # Обработка обновления через aiogram
        update = types.Update(**data)
        await dp.process_update(update)
        
        return JSONResponse(content={"ok": True})
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)

# FastAPI эндпоинт для проверки статуса
@app.get("/api/status")
async def status():
    try:
        me = await bot.get_me()
        return {"status": "ok", "bot_info": me.to_python()}
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса: {e}")
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)

# FastAPI эндпоинт для установки вебхука
@app.post("/api/set-webhook")
async def set_webhook(request: Request):
    try:
        data = await request.json()
        webhook_url = data.get("url")
        
        if not webhook_url:
            return JSONResponse(content={"success": False, "error": "URL не указан"}, status_code=400)
        
        # Формируем полный URL вебхука
        full_webhook_url = f"{webhook_url}{WEBHOOK_PATH}"
        
        # Удаляем текущий вебхук
        await bot.delete_webhook()
        
        # Устанавливаем новый вебхук
        await bot.set_webhook(full_webhook_url)
        
        # Получаем информацию о вебхуке
        webhook_info = await bot.get_webhook_info()
        
        return {
            "success": True,
            "webhook_url": full_webhook_url,
            "webhook_info": webhook_info.to_python()
        }
    except Exception as e:
        logger.error(f"Ошибка при установке вебхука: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

# FastAPI эндпоинт для отправки тестового сообщения
@app.post("/api/send-test-message")
async def send_test_message(request: Request):
    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        
        if not chat_id:
            return JSONResponse(content={"success": False, "error": "ID чата не указан"}, status_code=400)
        
        # Отправляем тестовое сообщение
        message = await bot.send_message(
            chat_id=chat_id,
            text="Тестовое сообщение от бота. Если вы видите это сообщение, значит бот работает корректно!"
        )
        
        return {
            "success": True,
            "message_info": message.to_python()
        }
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

# Функция для запуска бота в режиме вебхука
async def on_startup(dp):
    logger.info(f"Запуск бота в режиме вебхука на {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)

# Функция для остановки бота
async def on_shutdown(dp):
    logger.info("Остановка бота")
    await bot.delete_webhook()

# Точка входа для запуска бота через uvicorn
if __name__ == "__main__":
    # Запускаем FastAPI с uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

