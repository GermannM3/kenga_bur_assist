import { NextResponse } from "next/server"

// Простой эндпоинт для проверки статуса API
export async function GET() {
  try {
    return NextResponse.json({
      status: "API is running",
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error("Error in webhook-status route:", error)
    return NextResponse.json(
      {
        error: "Error checking API status",
        details: String(error),
      },
      { status: 500 },
    )
  }
}

