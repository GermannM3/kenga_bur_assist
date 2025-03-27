import { NextResponse } from "next/server"
import { headers } from "next/headers"

export async function GET() {
  try {
    // Получаем базовый URL из заголовков запроса
    const headersList = headers()
    const host = headersList.get("host") || "localhost:3000"
    const protocol = host.includes("localhost") ? "http" : "https"
    const baseUrl = `${protocol}://${host}`

    console.log("Base URL for debug webhook:", baseUrl)

    // Вызываем Python-функцию для получения отладочной информации
    const response = await fetch(`${baseUrl}/api/debug`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error in GET /api/debug-webhook:", error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}

