import TelegramBot from "node-telegram-bot-api"
import {
  getDistricts,
  getDepthsForDistrict,
  getEquipmentList,
  getServicesList,
  calculateTotalCost,
  getHorizonInfo,
  calculateDrillingCost,
} from "./drilling-data"

// Проверяем наличие токена
if (!process.env.TELEGRAM_BOT_TOKEN) {
  throw new Error("TELEGRAM_BOT_TOKEN is not defined")
}

// Инициализация бота с правильными параметрами для webhook режима
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, {
  polling: false,
  filepath: false, // Важно для Vercel - не использовать файловую систему
})

console.log("Bot initialized with token:", process.env.TELEGRAM_BOT_TOKEN.substring(0, 5) + "...")

// Хранение состояния пользователей
type UserState = {
  stage: "initial" | "district_selected" | "depth_selected" | "equipment_selection" | "services_selection" | "final"
  district?: string
  depth?: number
  selectedEquipment: string[]
  selectedServices: string[]
}

// Используем Map вместо объекта для лучшей производительности
const userStates = new Map<number, UserState>()

// Обработка входящих обновлений
export async function processUpdate(update: any) {
  try {
    console.log("Processing update:", JSON.stringify(update))

    if (!update.message && !update.callback_query) {
      console.log("Update does not contain message or callback_query")
      return
    }

    const chatId = update.message?.chat.id || update.callback_query?.message.chat.id
    console.log("Chat ID:", chatId)

    // Инициализация состояния пользователя, если его нет
    if (!userStates.has(chatId)) {
      console.log("Initializing user state for chat ID:", chatId)
      userStates.set(chatId, {
        stage: "initial",
        selectedEquipment: [],
        selectedServices: [],
      })
    }

    // Обработка команд
    if (update.message?.text) {
      const text = update.message.text
      console.log("Received text message:", text)

      if (text === "/start") {
        console.log("Processing /start command")
        await startBot(chatId)
        return
      }

      if (text === "/reset") {
        console.log("Processing /reset command")
        userStates.set(chatId, {
          stage: "initial",
          selectedEquipment: [],
          selectedServices: [],
        })
        await startBot(chatId)
        return
      }

      // Если не распознали команду, отправляем приветственное сообщение
      console.log("Unrecognized command, sending welcome message")
      await startBot(chatId)
      return
    }

    // Обработка нажатий на кнопки
    if (update.callback_query) {
      const data = update.callback_query.data
      const messageId = update.callback_query.message.message_id
      console.log("Received callback query with data:", data)

      try {
        // Подтверждаем получение callback query
        await bot.answerCallbackQuery(update.callback_query.id)
        console.log("Answered callback query")

        if (data.startsWith("district_")) {
          const district = data.replace("district_", "")
          console.log("Selected district:", district)
          await handleDistrictSelection(chatId, district, messageId)
        } else if (data.startsWith("depth_")) {
          const depth = Number.parseInt(data.replace("depth_", ""))
          console.log("Selected depth:", depth)
          await handleDepthSelection(chatId, depth, messageId)
        } else if (data.startsWith("equipment_")) {
          const equipment = data.replace("equipment_", "")
          console.log("Selected equipment:", equipment)
          await handleEquipmentSelection(chatId, equipment, messageId)
        } else if (data === "equipment_done") {
          console.log("Equipment selection done")
          await showServicesSelection(chatId, messageId)
        } else if (data.startsWith("service_")) {
          const service = data.replace("service_", "")
          console.log("Selected service:", service)
          await handleServiceSelection(chatId, service, messageId)
        } else if (data === "services_done") {
          console.log("Services selection done")
          await showFinalCalculation(chatId, messageId)
        } else if (data === "start_over") {
          console.log("Starting over")
          userStates.set(chatId, {
            stage: "initial",
            selectedEquipment: [],
            selectedServices: [],
          })
          await startBot(chatId)
        }
      } catch (error) {
        console.error("Error processing callback query:", error)
      }
    }
  } catch (error) {
    console.error("Error in processUpdate:", error)
    // Пытаемся отправить сообщение об ошибке пользователю
    try {
      const chatId = update.message?.chat.id || update.callback_query?.message.chat.id
      if (chatId) {
        await bot.sendMessage(
          chatId,
          "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или отправьте /start для перезапуска бота.",
        )
      }
    } catch (sendError) {
      console.error("Error sending error message:", sendError)
    }
  }
}

// Начало работы с ботом
async function startBot(chatId: number) {
  try {
    console.log("Starting bot for chat ID:", chatId)

    // Отправляем простое сообщение для проверки соединения
    await bot.sendMessage(chatId, "Подключение к боту... Пожалуйста, подождите.")
    console.log("Connection test message sent")

    const districts = getDistricts()

    // Группируем районы для более удобного отображения (по 2 в строке)
    const districtGroups: string[][] = []
    for (let i = 0; i < districts.length; i += 2) {
      districtGroups.push(districts.slice(i, i + 2))
    }

    const keyboard = {
      inline_keyboard: districtGroups.map((group) =>
        group.map((district) => ({ text: district, callback_data: `district_${district}` })),
      ),
    }

    console.log("Sending welcome message with keyboard")
    await bot.sendMessage(chatId, "Добро пожаловать в калькулятор стоимости бурения! Выберите район:", {
      reply_markup: keyboard,
    })
    console.log("Welcome message sent")

    const state = userStates.get(chatId)
    if (state) {
      state.stage = "initial"
    }
  } catch (error) {
    console.error("Error in startBot:", error)
    // Пробуем отправить простое сообщение без клавиатуры
    try {
      await bot.sendMessage(
        chatId,
        "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже или обратитесь к администратору.",
      )
    } catch (sendError) {
      console.error("Error sending error message:", sendError)
    }
  }
}

// Обработка выбора района
async function handleDistrictSelection(chatId: number, district: string, messageId: number) {
  try {
    console.log(`Handling district selection for chat ID: ${chatId}, district: ${district}`)

    // Получаем текущее состояние пользователя
    const currentState = userStates.get(chatId) || {
      stage: "initial",
      selectedEquipment: [],
      selectedServices: [],
    }

    // Обновляем состояние
    userStates.set(chatId, {
      ...currentState,
      district: district,
      stage: "district_selected",
    })

    const depths = getDepthsForDistrict(district)

    // Проверяем, есть ли глубины для выбранного района
    if (depths.length === 0) {
      await bot.editMessageText(
        `К сожалению, для района "${district}" нет доступных данных о глубинах бурения. Пожалуйста, выберите другой район.`,
        {
          chat_id: chatId,
          message_id: messageId,
        },
      )

      // Отправляем новое сообщение с выбором района
      await startBot(chatId)
      return
    }

    // Группируем глубины для более удобного отображения (по 3 в строке)
    const depthGroups: number[][] = []
    for (let i = 0; i < depths.length; i += 3) {
      depthGroups.push(depths.slice(i, i + 3))
    }

    const keyboard = {
      inline_keyboard: depthGroups.map((group) =>
        group.map((depth) => ({ text: `${depth} м`, callback_data: `depth_${depth}` })),
      ),
    }

    // Получаем информацию о горизонтах для этого района
    const horizonInfo = getHorizonInfo(district)
    let horizonText = ""

    if (horizonInfo) {
      if (horizonInfo.pi1) {
        horizonText += `\nПервый водоносный горизонт (ПИ1): ${horizonInfo.pi1[0]}-${horizonInfo.pi1[1]} м`
      }
      if (horizonInfo.pi2) {
        horizonText += `\nВторой водоносный горизонт (ПИ2): ${horizonInfo.pi2[0]}-${horizonInfo.pi2[1]} м`
      }
    }

    await bot.editMessageText(`Вы выбрали район: ${district}${horizonText}\n\nВыберите глубину бурения:`, {
      chat_id: chatId,
      message_id: messageId,
      reply_markup: keyboard,
    })
    console.log("Depth selection message sent")
  } catch (error) {
    console.error("Error in handleDistrictSelection:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при выборе района. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Обработка выбора глубины
async function handleDepthSelection(chatId: number, depth: number, messageId: number) {
  try {
    console.log(`Handling depth selection for chat ID: ${chatId}, depth: ${depth}`)
    const state = userStates.get(chatId)
    if (!state) {
      console.error("No state found for chat ID:", chatId)
      await bot.sendMessage(chatId, "Произошла ошибка. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    if (!state.district) {
      console.error("No district selected for chat ID:", chatId)
      await bot.sendMessage(chatId, "Сначала выберите район. Отправьте /start для перезапуска.")
      return
    }

    userStates.set(chatId, {
      ...state,
      depth: depth,
      stage: "depth_selected",
    })

    // Рассчитываем стоимость бурения
    const drillingCost = calculateDrillingCost(state.district, depth)

    const equipmentList = getEquipmentList()

    // Группируем оборудование для более удобного отображения (по 1 в строке)
    const equipmentGroups: string[][] = []
    for (let i = 0; i < equipmentList.length; i += 1) {
      equipmentGroups.push(equipmentList.slice(i, i + 1))
    }

    const keyboard = {
      inline_keyboard: [
        ...equipmentGroups.map((group) => group.map((item) => ({ text: item, callback_data: `equipment_${item}` }))),
        [{ text: "Завершить выбор оборудования", callback_data: "equipment_done" }],
      ],
    }

    await bot.editMessageText(
      `Вы выбрали глубину: ${depth} м\n\nСтоимость бурения: ${drillingCost.toLocaleString("ru-RU")} руб.\n\nВыберите необходимое оборудование:`,
      {
        chat_id: chatId,
        message_id: messageId,
        reply_markup: keyboard,
      },
    )
    console.log("Equipment selection message sent")
  } catch (error) {
    console.error("Error in handleDepthSelection:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при выборе глубины. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Обработка выбора оборудования
async function handleEquipmentSelection(chatId: number, equipment: string, messageId: number) {
  try {
    console.log(`Handling equipment selection for chat ID: ${chatId}, equipment: ${equipment}`)
    const state = userStates.get(chatId)
    if (!state) {
      console.error("No state found for chat ID:", chatId)
      await bot.sendMessage(chatId, "Произошла ошибка. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    // Создаем копию массива выбранного оборудования
    const selectedEquipment = [...state.selectedEquipment]

    // Добавляем или удаляем оборудование из списка
    const index = selectedEquipment.indexOf(equipment)
    if (index === -1) {
      selectedEquipment.push(equipment)
    } else {
      selectedEquipment.splice(index, 1)
    }

    // Обновляем состояние пользователя
    userStates.set(chatId, {
      ...state,
      selectedEquipment,
      stage: "equipment_selection",
    })

    // Получаем список всего оборудования
    const equipmentList = getEquipmentList()

    // Группируем оборудование для более удобного отображения (по 1 в строке)
    const equipmentGroups: string[][] = []
    for (let i = 0; i < equipmentList.length; i += 1) {
      equipmentGroups.push(equipmentList.slice(i, i + 1))
    }

    // Создаем клавиатуру с отметками выбранного оборудования
    const keyboard = {
      inline_keyboard: [
        ...equipmentGroups.map((group) =>
          group.map((item) => ({
            text: selectedEquipment.includes(item) ? `✅ ${item}` : item,
            callback_data: `equipment_${item}`,
          })),
        ),
        [{ text: "Завершить выбор оборудования", callback_data: "equipment_done" }],
      ],
    }

    // Формируем текст сообщения
    let messageText = "Выбранное оборудование:\n"
    if (selectedEquipment.length > 0) {
      messageText += selectedEquipment.map((e) => `- ${e}`).join("\n")
    } else {
      messageText += "Ничего не выбрано"
    }

    await bot.editMessageText(messageText, {
      chat_id: chatId,
      message_id: messageId,
      reply_markup: keyboard,
    })
    console.log("Equipment selection message updated")
  } catch (error) {
    console.error("Error in handleEquipmentSelection:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при выборе оборудования. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Показ выбора услуг
async function showServicesSelection(chatId: number, messageId: number) {
  try {
    console.log(`Showing services selection for chat ID: ${chatId}`)
    const state = userStates.get(chatId)
    if (!state) {
      console.error("No state found for chat ID:", chatId)
      await bot.sendMessage(chatId, "Произошла ошибка. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    const services = getServicesList()

    // Группируем услуги для более удобного отображения (по 1 в строке)
    const serviceGroups: string[][] = []
    for (let i = 0; i < services.length; i += 1) {
      serviceGroups.push(services.slice(i, i + 1))
    }

    const keyboard = {
      inline_keyboard: [
        ...serviceGroups.map((group) => group.map((item) => ({ text: item, callback_data: `service_${item}` }))),
        [{ text: "Завершить выбор услуг", callback_data: "services_done" }],
      ],
    }

    // Формируем текст сообщения
    let messageText = "Выбранное оборудование:\n"
    if (state.selectedEquipment.length > 0) {
      messageText += state.selectedEquipment.map((e) => `- ${e}`).join("\n")
    } else {
      messageText += "Ничего не выбрано"
    }

    messageText += "\n\nВыберите дополнительные услуги:"

    await bot.editMessageText(messageText, {
      chat_id: chatId,
      message_id: messageId,
      reply_markup: keyboard,
    })
    console.log("Services selection message sent")

    state.stage = "services_selection"
  } catch (error) {
    console.error("Error in showServicesSelection:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при выборе услуг. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Обработка выбора услуг
async function handleServiceSelection(chatId: number, service: string, messageId: number) {
  try {
    console.log(`Handling service selection for chat ID: ${chatId}, service: ${service}`)
    const state = userStates.get(chatId)
    if (!state) {
      console.error("No state found for chat ID:", chatId)
      await bot.sendMessage(chatId, "Произошла ошибка. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    // Создаем копию массива выбранных услуг
    const selectedServices = [...state.selectedServices]

    // Добавляем или удаляем услугу из списка
    const index = selectedServices.indexOf(service)
    if (index === -1) {
      selectedServices.push(service)
    } else {
      selectedServices.splice(index, 1)
    }

    // Обновляем состояние пользователя
    userStates.set(chatId, { ...state, selectedServices })

    // Получаем список всех услуг
    const servicesList = getServicesList()

    // Группируем услуги для более удобного отображения (по 1 в строке)
    const serviceGroups: string[][] = []
    for (let i = 0; i < servicesList.length; i += 1) {
      serviceGroups.push(servicesList.slice(i, i + 1))
    }

    // Создаем клавиатуру с отметками выбранных услуг
    const keyboard = {
      inline_keyboard: [
        ...serviceGroups.map((group) =>
          group.map((item) => ({
            text: selectedServices.includes(item) ? `✅ ${item}` : item,
            callback_data: `service_${item}`,
          })),
        ),
        [{ text: "Завершить выбор услуг", callback_data: "services_done" }],
      ],
    }

    // Формируем текст сообщения
    let messageText = "Выбранное оборудование:\n"
    if (state.selectedEquipment.length > 0) {
      messageText += state.selectedEquipment.map((e) => `- ${e}`).join("\n")
    } else {
      messageText += "Ничего не выбрано"
    }

    messageText += "\n\nВыбранные услуги:\n"
    if (selectedServices.length > 0) {
      messageText += selectedServices.map((s) => `- ${s}`).join("\n")
    } else {
      messageText += "Ничего не выбрано"
    }

    await bot.editMessageText(messageText, {
      chat_id: chatId,
      message_id: messageId,
      reply_markup: keyboard,
    })
    console.log("Services selection message updated")
  } catch (error) {
    console.error("Error in handleServiceSelection:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при выборе услуг. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Показ финального расчета
async function showFinalCalculation(chatId: number, messageId: number) {
  try {
    console.log(`Showing final calculation for chat ID: ${chatId}`)
    const state = userStates.get(chatId)
    if (!state) {
      console.error("No state found for chat ID:", chatId)
      await bot.sendMessage(chatId, "Произошла ошибка. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    if (!state.district || !state.depth) {
      console.error("District or depth not selected for chat ID:", chatId)
      await bot.sendMessage(chatId, "Не выбран район или глубина. Пожалуйста, отправьте /start для перезапуска.")
      return
    }

    // Рассчитываем стоимость
    const drillingCost = calculateDrillingCost(state.district, state.depth)
    const totalCost = calculateTotalCost(state.district, state.depth, state.selectedEquipment, state.selectedServices)

    // Формируем сообщение с результатами
    let message = `📋 *Итоговый расчет*\n\n`
    message += `🏙️ Район: *${state.district}*\n`
    message += `🔍 Глубина бурения: *${state.depth} м*\n\n`
    message += `💧 Стоимость бурения: *${drillingCost.toLocaleString("ru-RU")} руб.*\n\n`

    message += `🛠️ Выбранное оборудование:\n`
    if (state.selectedEquipment.length > 0) {
      state.selectedEquipment.forEach((item) => {
        message += `- ${item}\n`
      })
    } else {
      message += `Не выбрано\n`
    }

    message += `\n🔧 Выбранные услуги:\n`
    if (state.selectedServices.length > 0) {
      state.selectedServices.forEach((item) => {
        message += `- ${item}\n`
      })
    } else {
      message += `Не выбрано\n`
    }

    message += `\n💰 *Итоговая стоимость: ${totalCost.toLocaleString("ru-RU")} руб.*`

    // Клавиатура для начала заново
    const keyboard = {
      inline_keyboard: [[{ text: "Начать заново", callback_data: "start_over" }]],
    }

    await bot.editMessageText(message, {
      chat_id: chatId,
      message_id: messageId,
      reply_markup: keyboard,
      parse_mode: "Markdown",
    })
    console.log("Final calculation message sent")

    state.stage = "final"
  } catch (error) {
    console.error("Error in showFinalCalculation:", error)
    await bot.sendMessage(
      chatId,
      "Произошла ошибка при расчете стоимости. Пожалуйста, попробуйте позже или отправьте /start для перезапуска.",
    )
  }
}

// Webhook для установки вебхука
export async function setWebhook(url: string) {
  try {
    // Если URL пустой, просто получаем информацию о текущем вебхуке
    if (!url) {
      console.log("Getting current webhook info")
      try {
        const webhookInfo = await bot.getWebHookInfo()
        console.log("Current webhook info:", webhookInfo)
        return { success: true, webhookInfo }
      } catch (webhookError) {
        console.error("Error getting webhook info:", webhookError)
        // Возвращаем ошибку в структурированном виде
        return {
          success: false,
          error: String(webhookError),
          errorType: "webhook_info_error",
        }
      }
    }

    // Формируем полный URL вебхука
    const webhookUrl = `${url}/api/telegram`
    console.log("Setting webhook to:", webhookUrl)

    // Удаляем текущий вебхук перед установкой нового
    console.log("Deleting current webhook")
    await bot.deleteWebHook()

    // Устанавливаем новый вебхук с максимальными настройками
    const result = await bot.setWebhook(webhookUrl, {
      max_connections: 100,
      drop_pending_updates: true,
    })
    console.log("Webhook set result:", result)

    // Получаем информацию о новом вебхуке
    const webhookInfo = await bot.getWebHookInfo()
    console.log("New webhook info:", webhookInfo)

    // Отправляем тестовое сообщение боту
    try {
      const me = await bot.getMe()
      console.log("Sending test message to bot")
      await bot.sendMessage(me.id, "Webhook setup test message")
      console.log("Test message sent")
    } catch (testError) {
      console.log("Could not send test message:", testError)
      // Это не критическая ошибка, продолжаем
    }

    return { success: result, webhookUrl, webhookInfo }
  } catch (error) {
    console.error("Error setting webhook:", error)
    return {
      success: false,
      error: String(error),
      errorType: "general_error",
    }
  }
}

// Функция для тестирования бота
export async function testBot() {
  try {
    console.log("Testing bot...")
    const me = await bot.getMe()
    console.log("Bot info:", me)

    // Проверяем текущий вебхук
    const webhookInfo = await bot.getWebHookInfo()
    console.log("Current webhook info:", webhookInfo)

    return {
      success: true,
      botInfo: me,
      webhookInfo,
    }
  } catch (error) {
    console.error("Error testing bot:", error)
    return { success: false, error: String(error) }
  }
}

// Функция для отправки тестового сообщения
export async function sendTestMessage(chatId: number) {
  try {
    console.log("Sending test message to chat ID:", chatId)
    const result = await bot.sendMessage(
      chatId,
      "Тестовое сообщение от бота. Если вы видите это сообщение, значит бот работает корректно!",
    )
    console.log("Test message sent:", result)
    return { success: true, messageInfo: result }
  } catch (error) {
    console.error("Error sending test message:", error)
    return { success: false, error: String(error) }
  }
}

// Экспортируем функции для использования в других модулях
export {
  handleDistrictSelection,
  handleDepthSelection,
  handleEquipmentSelection,
  showServicesSelection,
  handleServiceSelection,
  showFinalCalculation,
}

