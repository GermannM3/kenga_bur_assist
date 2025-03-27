import { NextResponse } from "next/server"
import { headers } from "next/headers"

export async function GET() {
  try {
    // Получаем базовый URL из заголовков запроса
    const headersList = headers()
    const host = headersList.get("host") || "localhost:3000"
    const protocol = host.includes("localhost") ? "http" : "https"
    const baseUrl = `${protocol}://${host}`

    console.log("Base URL for health check:", baseUrl)

    // Call the Python health check endpoint
    const response = await fetch(`${baseUrl}/api/health-check`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    // Add Next.js environment info
    return NextResponse.json({
      ...data,
      next_js_env: {
        host: host,
        protocol: protocol,
        baseUrl: baseUrl,
        NODE_ENV: process.env.NODE_ENV || "not set",
      },
    })
  } catch (error) {
    console.error("Error in GET /api/health:", error)
    return NextResponse.json(
      {
        status: "error",
        error: String(error),
        message: "Failed to check Python function health",
      },
      { status: 500 },
    )
  }
}

