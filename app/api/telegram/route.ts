import { NextResponse } from "next/server"

// Прокси для перенаправления запросов от Telegram к Python-боту
export async function POST(request: Request) {
  try {
    console.log("Получен запрос от Telegram, перенаправляем на Python-бота")

    // Получаем тело запроса
    const body = await request.text()
    console.log("Тело запроса:", body)

    // URL Python-бота (в production это будет URL вашего Python-сервиса)
    const botUrl = process.env.BOT_SERVICE_URL || "http://localhost:8000/api/telegram-webhook"

    // Перенаправляем запрос на Python-бота
    const response = await fetch(botUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body,
    })

    // Получаем ответ от Python-бота
    const responseData = await response.json()
    console.log("Ответ от Python-бота:", responseData)

    return NextResponse.json(responseData)
  } catch (error) {
    console.error("Ошибка при перенаправлении запроса на Python-бота:", error)
    return NextResponse.json({ error: "Ошибка при обработке запроса", details: String(error) }, { status: 500 })
  }
}

