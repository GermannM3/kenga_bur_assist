import { NextResponse } from "next/server"
import { headers } from "next/headers"

export async function GET() {
  try {
    // Получаем базовый URL из заголовков запроса
    const headersList = headers()
    const host = headersList.get("host") || "localhost:3000"
    const protocol = host.includes("localhost") ? "http" : "https"
    const baseUrl = `${protocol}://${host}`

    // Вызываем Python-функцию для проверки
    const response = await fetch(`${baseUrl}/api/test`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }).catch((error) => {
      console.error("Fetch error:", error)
      throw error
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Error response:", errorText)
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    // Добавляем информацию о Next.js
    return NextResponse.json({
      ...data,
      next_js_info: {
        host: host,
        protocol: protocol,
        baseUrl: baseUrl,
        NODE_ENV: process.env.NODE_ENV || "not set",
      },
    })
  } catch (error) {
    console.error("Error in GET /api/test:", error)
    return NextResponse.json(
      {
        status: "error",
        error: String(error),
        message: "Failed to check Python function",
      },
      { status: 500 },
    )
  }
}

