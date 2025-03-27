"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function TestPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Автоматически запускаем тест при загрузке страницы
  useEffect(() => {
    testBasicFunctionality()
  }, [])

  const testBasicFunctionality = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch("/api/test")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response:", errorText)
        throw new Error(`Failed to test basic functionality: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      console.error("Error testing basic functionality:", err)
      setError(err.message || "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Базовая проверка функциональности</CardTitle>
          <CardDescription>Проверка работоспособности Python-функций и API-маршрутов</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="flex justify-center mb-4">
            <Button onClick={testBasicFunctionality} disabled={isLoading} className="w-full max-w-xs">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Проверка...
                </>
              ) : (
                "Запустить проверку"
              )}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Ошибка</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <div className="space-y-4">
              <Alert className={result.status === "ok" ? "bg-green-50" : "bg-red-50"}>
                <AlertTitle>{result.status === "ok" ? "Проверка успешна" : "Ошибка проверки"}</AlertTitle>
                <AlertDescription>
                  {result.message ||
                    (result.status === "ok"
                      ? "Базовая функциональность работает"
                      : "Проблема с базовой функциональностью")}
                </AlertDescription>
              </Alert>

              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-medium mb-2">Информация о Python</h3>
                <p>
                  <strong>Версия Python:</strong> {result.python_version}
                </p>
                <p>
                  <strong>Путь запроса:</strong> {result.path}
                </p>
              </div>

              <div className="border rounded-lg p-4">
                <h3 className="text-lg font-medium mb-2">Заголовки запроса</h3>
                <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                  {JSON.stringify(result.headers, null, 2)}
                </pre>
              </div>

              {result.next_js_info && (
                <div className="border rounded-lg p-4">
                  <h3 className="text-lg font-medium mb-2">Информация о Next.js</h3>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                    {JSON.stringify(result.next_js_info, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </CardContent>

        <CardFooter className="flex-col items-start">
          <h3 className="text-lg font-medium mb-2">Что проверяет этот тест</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li>Работоспособность Python-функций на Vercel</li>
            <li>Правильность маршрутизации API-запросов</li>
            <li>Доступность переменных окружения</li>
            <li>Корректность заголовков запросов</li>
            <li>Взаимодействие между Next.js и Python</li>
          </ul>
        </CardFooter>
      </Card>
    </main>
  )
}

