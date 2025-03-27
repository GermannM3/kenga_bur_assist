"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Loader2, Upload } from "lucide-react"

export default function PdfUploadPage() {
  const [pricingFile, setPricingFile] = useState<File | null>(null)
  const [depthMapFile, setDepthMapFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handlePricingFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setPricingFile(e.target.files[0])
    }
  }

  const handleDepthMapFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setDepthMapFile(e.target.files[0])
    }
  }

  const uploadFiles = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    // Здесь будет код для загрузки файлов
    // В реальном приложении вы бы отправили файлы на сервер

    // Имитация загрузки
    setTimeout(() => {
      setResult({
        success: true,
        message: "Файлы успешно загружены и обработаны",
      })
      setIsLoading(false)
    }, 2000)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Загрузка PDF файлов</CardTitle>
          <CardDescription>Загрузите прайс-листы и карты глубин в формате PDF</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid w-full items-center gap-6">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="pricing-pdf">Прайс-лист (PDF)</Label>
              <div className="flex items-center gap-2">
                <input
                  id="pricing-pdf"
                  type="file"
                  accept=".pdf"
                  onChange={handlePricingFileChange}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => document.getElementById("pricing-pdf")?.click()}
                  className="w-full"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {pricingFile ? pricingFile.name : "Выбрать файл"}
                </Button>
              </div>
            </div>

            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="depth-map-pdf">Карта глубин (PDF)</Label>
              <div className="flex items-center gap-2">
                <input
                  id="depth-map-pdf"
                  type="file"
                  accept=".pdf"
                  onChange={handleDepthMapFileChange}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => document.getElementById("depth-map-pdf")?.click()}
                  className="w-full"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {depthMapFile ? depthMapFile.name : "Выбрать файл"}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col items-start gap-4">
          <Button onClick={uploadFiles} disabled={isLoading || !pricingFile || !depthMapFile} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Загрузка...
              </>
            ) : (
              "Загрузить файлы"
            )}
          </Button>

          {error && <div className="text-red-500 text-sm w-full">{error}</div>}

          {result && (
            <div className="text-sm w-full">
              <p className="font-medium text-green-600">{result.message}</p>
            </div>
          )}
        </CardFooter>
      </Card>
    </main>
  )
}

