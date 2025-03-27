import { NextResponse } from "next/server"
import { headers } from "next/headers"

export async function GET(request: Request) {
  try {
    // Получаем базовый URL из заголовков запроса
    const headersList = headers()
    const host = headersList.get("host") || "localhost:3000"
    const protocol = host.includes("localhost") ? "http" : "https"
    const baseUrl = `${protocol}://${host}`

    console.log("Base URL for webhook:", baseUrl)

    // Вызываем Python-функцию для получения информации о вебхуке
    const response = await fetch(`${baseUrl}/api/webhook-info`, {
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
    console.error("Error in GET /api/setup-webhook:", error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const { url } = await request.json()

    if (!url) {
      // Если URL не предоставлен, используем URL из заголовков
      const headersList = headers()
      const host = headersList.get("host") || "localhost:3000"
      const protocol = host.includes("localhost") ? "http" : "https"
      const baseUrl = `${protocol}://${host}`

      console.log("Using base URL from headers:", baseUrl)

      // Вызываем Python-функцию для установки вебхука
      const response = await fetch(`${baseUrl}/api/set-webhook`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: baseUrl }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return NextResponse.json(data)
    } else {
      // Если URL предоставлен, используем его
      console.log("Using provided URL:", url)

      // Вызываем Python-функцию для установки вебхука
      const response = await fetch(`${url}/api/set-webhook`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return NextResponse.json(data)
    }
  } catch (error) {
    console.error("Error in POST /api/setup-webhook:", error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}

