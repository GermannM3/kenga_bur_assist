import { NextResponse } from "next/server"
import { headers } from "next/headers"

export async function GET() {
  try {
    // Получаем заголовки запроса для определения хоста
    const headersList = headers()
    const host = headersList.get("host") || "localhost:3000"
    const protocol = host.includes("localhost") ? "http" : "https"
    const baseUrl = `${protocol}://${host}`

    console.log("Базовый URL из заголовков:", baseUrl)

    // Проверяем работу Next.js API напрямую
    try {
      console.log("Проверка Next.js API")
      const nextJsResponse = await fetch(`${baseUrl}/api/hello`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (nextJsResponse.ok) {
        const nextJsData = await nextJsResponse.json()
        console.log("Next.js API работает:", nextJsData)
      } else {
        console.error("Next.js API не работает:", await nextJsResponse.text())
      }
    } catch (nextJsError) {
      console.error("Ошибка при проверке Next.js API:", nextJsError)
    }

    // Вместо прямого вызова Python API, вернем информацию о текущем окружении
    return NextResponse.json({
      status: "ok",
      message: "Проверка окружения",
      environment: {
        NODE_ENV: process.env.NODE_ENV || "not set",
        VERCEL_URL: process.env.VERCEL_URL || "not set",
        NEXT_PUBLIC_VERCEL_URL: process.env.NEXT_PUBLIC_VERCEL_URL || "not set",
        BOT_SERVICE_URL: process.env.BOT_SERVICE_URL || "not set",
      },
      request_info: {
        host: host,
        protocol: protocol,
        baseUrl: baseUrl,
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error("Ошибка в GET /api/check:", error)

    // Возвращаем подробную информацию об ошибке
    return NextResponse.json(
      {
        status: "error",
        error: String(error),
        message: "Ошибка при проверке окружения",
        debug_info: {
          error_type: error instanceof Error ? error.name : "Unknown",
          stack: error instanceof Error ? error.stack : "No stack available",
        },
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    )
  }
}

