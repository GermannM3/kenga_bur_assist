"use client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Telegram бот для расчета стоимости бурения</CardTitle>
          <CardDescription>Инструменты для настройки и отладки бота</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>
            Этот проект представляет собой Telegram-бота для расчета стоимости бурения скважин. Бот реализован на Python
            с использованием python-telegram-bot и развернут на Vercel.
          </p>
          <div className="grid grid-cols-1 gap-4">
            <Link href="/check" className="w-full">
              <Button className="w-full">Проверить API</Button>
            </Link>
            <Link href="/debug" className="w-full">
              <Button variant="outline" className="w-full">
                Отладка бота
              </Button>
            </Link>
          </div>
        </CardContent>
        <CardFooter>
          <p className="text-sm text-gray-500">
            Для работы бота необходимо настроить вебхук и убедиться, что Python API работает корректно.
          </p>
        </CardFooter>
      </Card>
    </main>
  )
}

