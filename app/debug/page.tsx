"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function DebugPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [isCheckingHealth, setIsCheckingHealth] = useState(false)
  const [isTestingBasic, setIsTestingBasic] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [healthInfo, setHealthInfo] = useState<any>(null)
  const [testResult, setTestResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const runDiagnostics = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch("/api/debug-webhook")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response:", errorText)
        throw new Error(`Failed to run diagnostics: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      console.error("Error running diagnostics:", err)
      setError(err.message || "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  const checkHealth = async () => {
    setIsCheckingHealth(true)
    setError(null)
    setHealthInfo(null)

    try {
      const response = await fetch("/api/health")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response:", errorText)
        throw new Error(`Failed to check health: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setHealthInfo(data)
    } catch (err: any) {
      console.error("Error checking health:", err)
      setError(err.message || "An error occurred")
    } finally {
      setIsCheckingHealth(false)
    }
  }

  const testBasicFunctionality = async () => {
    setIsTestingBasic(true)
    setError(null)
    setTestResult(null)

    try {
      const response = await fetch("/api/test")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Error response:", errorText)
        throw new Error(`Failed to test basic functionality: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      setTestResult(data)
    } catch (err: any) {
      console.error("Error testing basic functionality:", err)
      setError(err.message || "An error occurred")
    } finally {
      setIsTestingBasic(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-3xl">
        <CardHeader>
          <CardTitle>Диагностика Telegram бота</CardTitle>
          <CardDescription>Расширенная диагностика для выявления проблем с ботом</CardDescription>
        </CardHeader>

        <Tabs defaultValue="basic">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Базовая проверка</TabsTrigger>
            <TabsTrigger value="diagnostics">Диагностика бота</TabsTrigger>
            <TabsTrigger value="health">Проверка системы</TabsTrigger>
          </TabsList>

          <TabsContent value="basic">
            <CardContent>
              <div className="flex justify-center mb-4">
                <Button onClick={testBasicFunctionality} disabled={isTestingBasic} className="w-full max-w-xs">
                  {isTestingBasic ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Проверка...
                    </>
                  ) : (
                    "Проверить базовую функциональность"
                  )}
                </Button>
              </div>

              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertTitle>Ошибка</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {testResult && (
                <div className="space-y-4">
                  <Alert className={testResult.status === "ok" ? "bg-green-50" : "bg-red-50"}>
                    <AlertTitle>{testResult.status === "ok" ? "Проверка успешна" : "Ошибка проверки"}</AlertTitle>
                    <AlertDescription>
                      {testResult.message ||
                        (testResult.status === "ok"
                          ? "Базовая функциональность работает"
                          : "Проблема с базовой функциональностью")}
                    </AlertDescription>
                  </Alert>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Информация о Python</h3>
                    <p>
                      <strong>Версия Python:</strong> {testResult.python_version}
                    </p>
                    <p>
                      <strong>Путь запроса:</strong> {testResult.path}
                    </p>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Заголовки запроса</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                      {JSON.stringify(testResult.headers, null, 2)}
                    </pre>
                  </div>

                  {testResult.next_js_info && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Информация о Next.js</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(testResult.next_js_info, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </TabsContent>

          <TabsContent value="diagnostics">
            <CardContent>
              <div className="flex justify-center mb-4">
                <Button onClick={runDiagnostics} disabled={isLoading} className="w-full max-w-xs">
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Диагностика...
                    </>
                  ) : (
                    "Запустить диагностику"
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
                  <Alert className={result.success ? "bg-green-50" : "bg-red-50"}>
                    <AlertTitle>{result.success ? "Диагностика выполнена" : "Ошибка диагностики"}</AlertTitle>
                    <AlertDescription>
                      {result.success ? "Диагностика успешно выполнена" : result.error}
                    </AlertDescription>
                  </Alert>

                  {result.botInfo && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Информация о боте</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(result.botInfo, null, 2)}
                      </pre>
                    </div>
                  )}

                  {result.webhookInfo && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Информация о вебхуке</h3>
                      <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                        {JSON.stringify(result.webhookInfo, null, 2)}
                      </pre>
                    </div>
                  )}

                  {result.diagnostics && (
                    <div className="border rounded-lg p-4">
                      <h3 className="text-lg font-medium mb-2">Результаты диагностики</h3>
                      <div className="space-y-2">
                        <div className="flex items-center">
                          <div
                            className={`w-4 h-4 rounded-full mr-2 ${result.diagnostics.isWebhookSet ? "bg-green-500" : "bg-red-500"}`}
                          ></div>
                          <span>Вебхук установлен: {result.diagnostics.isWebhookSet ? "Да" : "Нет"}</span>
                        </div>
                        <div className="flex items-center">
                          <div
                            className={`w-4 h-4 rounded-full mr-2 ${!result.diagnostics.hasWebhookErrors ? "bg-green-500" : "bg-red-500"}`}
                          ></div>
                          <span>Ошибки вебхука: {result.diagnostics.hasWebhookErrors ? "Есть" : "Нет"}</span>
                        </div>
                        <div className="flex items-center">
                          <div
                            className={`w-4 h-4 rounded-full mr-2 ${!result.diagnostics.hasPendingUpdates ? "bg-green-500" : "bg-yellow-500"}`}
                          ></div>
                          <span>Ожидающие обновления: {result.diagnostics.hasPendingUpdates ? "Есть" : "Нет"}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </TabsContent>

          <TabsContent value="health">
            <CardContent>
              <div className="flex justify-center mb-4">
                <Button onClick={checkHealth} disabled={isCheckingHealth} className="w-full max-w-xs">
                  {isCheckingHealth ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Проверка...
                    </>
                  ) : (
                    "Проверить работоспособность"
                  )}
                </Button>
              </div>

              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertTitle>Ошибка</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {healthInfo && (
                <div className="space-y-4">
                  <Alert className={healthInfo.status === "ok" ? "bg-green-50" : "bg-red-50"}>
                    <AlertTitle>{healthInfo.status === "ok" ? "Система работает" : "Ошибка системы"}</AlertTitle>
                    <AlertDescription>
                      {healthInfo.message ||
                        (healthInfo.status === "ok"
                          ? "Все компоненты работают нормально"
                          : "Обнаружены проблемы в работе системы")}
                    </AlertDescription>
                  </Alert>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Переменные окружения Python</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                      {JSON.stringify(healthInfo.environment, null, 2)}
                    </pre>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Переменные окружения Next.js</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">
                      {JSON.stringify(healthInfo.next_js_env, null, 2)}
                    </pre>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h3 className="text-lg font-medium mb-2">Информация о системе</h3>
                    <p>
                      <strong>Python версия:</strong> {healthInfo.python_version}
                    </p>
                    <p>
                      <strong>Node.js окружение:</strong> {healthInfo.next_js_env?.NODE_ENV}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </TabsContent>
        </Tabs>

        <CardFooter className="flex-col items-start">
          <h3 className="text-lg font-medium mb-2">Рекомендации по устранению проблем</h3>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Убедитесь, что токен бота правильный и активен</li>
            <li>Проверьте, что вебхук установлен на правильный URL</li>
            <li>Убедитесь, что URL вашего сервера доступен из интернета</li>
            <li>Проверьте, что в URL вебхука указан правильный путь (/api/telegram)</li>
            <li>Если есть ошибки вебхука, проверьте логи на Vercel</li>
            <li>Попробуйте удалить и заново установить вебхук</li>
            <li>Проверьте, что бот добавлен в чат или группу, где вы пытаетесь его использовать</li>
            <li>Убедитесь, что все переменные окружения правильно настроены</li>
          </ol>
        </CardFooter>
      </Card>
    </main>
  )
}

