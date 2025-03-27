"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function CheckPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [isNextJsLoading, setIsNextJsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [nextJsResult, setNextJsResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [nextJsError, setNextJsError] = useState<string | null>(null)

  // Автоматически запускаем проверку при загрузке страницы
  useEffect(() => {
    checkAPI()
  }, [])

  const checkAPI = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch("/api/check")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Ошибка ответа:", errorText)
        throw new Error(`Ошибка при проверке API: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      console.error("Ошибка при проверке API:", err)
      setError(err.message || "Произошла ошибка")
    } finally {
      setIsLoading(false)
    }
  }

  const checkNextJsAPI = async () => {
    setIsNextJsLoading(true)
    setNextJsError(null)
    setNextJsResult(null)

    try {
      // Проверяем работу Next.js API
      const response = await fetch("/api/hello")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Ошибка Next.js API:", errorText)
        throw new Error(`Ошибка при проверке Next.js API: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setNextJsResult(data)
    } catch (err: any) {
      console.error("Ошибка при проверке Next.js API:", err)
      setNextJsError(err.message || "Произошла ошибка")
    } finally {
      setIsNextJsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Проверка API</CardTitle>
          <CardDescription>Проверка работоспособности API на Vercel</CardDescription>
        </CardHeader>

        <Tabs defaultValue="environment">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="environment">Окружение</TabsTrigger>
            <TabsTrigger value="nextjs-api">Next.js API</TabsTrigger>
          </TabsList>

          <TabsContent value="environment">
            <CardContent>
              <div className="flex justify-center mb-4">
                <Button onClick={checkAPI} disabled={isLoading} className="w-full max-w-xs">
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Проверка...
                    </>
                  ) : (
                    "Проверить окружение"
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
                        (result.status === "ok" ? "Окружение проверено" : "Проблема с проверкой окружения")}
                    </AlertDescription>
                  </Alert>

                  {result.environment && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Переменные окружения</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(result.environment, null, 2)}
                      </pre>
                    </div>
                  )}

                  {result.request_info && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Информация о запросе</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(result.request_info, null, 2)}
                      </pre>
                    </div>
                  )}

                  {result.debug_info && (
                    <div className="border rounded-lg p-4 bg-red-50">
                      <h3 className="text-lg font-medium mb-2">Отладочная информация</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(result.debug_info, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </TabsContent>

          <TabsContent value="nextjs-api">
            <CardContent>
              <div className="flex justify-center mb-4">
                <Button onClick={checkNextJsAPI} disabled={isNextJsLoading} className="w-full max-w-xs">
                  {isNextJsLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Проверка...
                    </>
                  ) : (
                    "Проверить Next.js API"
                  )}
                </Button>
              </div>

              {nextJsError && (
                <Alert variant="destructive" className="mb-4">
                  <AlertTitle>Ошибка</AlertTitle>
                  <AlertDescription>{nextJsError}</AlertDescription>
                </Alert>
              )}

              {nextJsResult && (
                <div className="space-y-4">
                  <Alert className={nextJsResult.status === "ok" ? "bg-green-50" : "bg-red-50"}>
                    <AlertTitle>
                      {nextJsResult.status === "ok" ? "Next.js API работает" : "Ошибка Next.js API"}
                    </AlertTitle>
                    <AlertDescription>
                      {nextJsResult.message ||
                        (nextJsResult.status === "ok" ? "Next.js API работает корректно" : "Проблема с Next.js API")}
                    </AlertDescription>
                  </Alert>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Информация о Next.js API</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                      {JSON.stringify(nextJsResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </CardContent>
          </TabsContent>
        </Tabs>

        <CardFooter className="flex-col items-start">
          <h3 className="text-lg font-medium mb-2">Что проверяет этот тест</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li>Доступность переменных окружения</li>
            <li>Информацию о запросе и хосте</li>
            <li>Работоспособность Next.js API</li>
            <li>Корректность заголовков запросов</li>
          </ul>
        </CardFooter>
      </Card>
    </main>
  )
}

