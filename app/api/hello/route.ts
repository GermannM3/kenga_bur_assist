import { NextResponse } from "next/server"

export async function GET() {
  return NextResponse.json({
    status: "ok",
    message: "Next.js API работает",
    timestamp: new Date().toISOString(),
  })
}

