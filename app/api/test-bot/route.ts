import { NextResponse } from "next/server"
import { testBot } from "@/lib/telegram-bot"

export async function GET() {
  try {
    const result = await testBot()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Error testing bot:", error)
    return NextResponse.json({ error: "Failed to test bot", details: String(error) }, { status: 500 })
  }
}

