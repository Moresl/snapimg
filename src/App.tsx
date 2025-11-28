import JSZip from 'jszip'
import { Download, Eye, Github, Loader2, Moon, Sun, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ImageCompare } from './components/ImageCompare'
import { UploadZone } from './components/UploadZone'
import { Button } from './components/ui/button'
import { Card, CardContent } from './components/ui/card'
import { Progress } from './components/ui/progress'
import { ToggleGroup, ToggleGroupItem } from './components/ui/toggle-group'
import { compressSingleImage, formatSize, type CompressResult, type OutputFormat } from './lib/api'
import { cn } from './lib/utils'

type FileStatus = 'pending' | 'compressing' | 'done' | 'error'

interface FileItem {
  id: string
  file: File
  status: FileStatus
  progress: number
  result?: CompressResult
  originalUrl: string
}

// 主题切换 Hook
function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    return false
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  return { isDark, toggle: () => setIsDark(!isDark) }
}

const FORMAT_OPTIONS: { value: OutputFormat; label: string }[] = [
  { value: 'original', label: '原格式' },
  { value: 'webp', label: 'WebP' },
  { value: 'png', label: 'PNG' },
  { value: 'jpeg', label: 'JPEG' },
]

function App() {
  const { isDark, toggle: toggleTheme } = useTheme()
  const [files, setFiles] = useState<FileItem[]>([])
  const [isCompressing, setIsCompressing] = useState(false)
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('original')
  const [compareData, setCompareData] = useState<{ originalUrl: string; compressedUrl: string; filename: string } | null>(null)
  const progressIntervals = useRef<Map<string, NodeJS.Timeout>>(new Map())

  useEffect(() => {
    return () => {
      progressIntervals.current.forEach(interval => clearInterval(interval))
    }
  }, [])

  const startProgress = (id: string) => {
    const interval = setInterval(() => {
      setFiles(prev => prev.map(f => {
        if (f.id === id && f.status === 'compressing' && f.progress < 90) {
          const increment = Math.max(1, (90 - f.progress) / 10)
          return { ...f, progress: Math.min(90, f.progress + increment) }
        }
        return f
      }))
    }, 100)
    progressIntervals.current.set(id, interval)
  }

  const stopProgress = (id: string) => {
    const interval = progressIntervals.current.get(id)
    if (interval) {
      clearInterval(interval)
      progressIntervals.current.delete(id)
    }
  }

  const handleFilesSelected = async (selectedFiles: File[]) => {
    const newFiles: FileItem[] = selectedFiles.map(file => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      status: 'pending' as FileStatus,
      progress: 0,
      originalUrl: URL.createObjectURL(file)
    }))
    setFiles(newFiles)
    setIsCompressing(true)

    for (let i = 0; i < newFiles.length; i++) {
      const currentFile = newFiles[i]
      setFiles(prev => prev.map((f, idx) =>
        idx === i ? { ...f, status: 'compressing', progress: 0 } : f
      ))
      startProgress(currentFile.id)

      try {
        const result = await compressSingleImage(currentFile.file, outputFormat)
        stopProgress(currentFile.id)
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: result.success ? 'done' : 'error', progress: 100, result } : f
        ))
      } catch (error) {
        stopProgress(currentFile.id)
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? {
            ...f, status: 'error', progress: 100,
            result: { filename: currentFile.file.name, original_size: currentFile.file.size, compressed_size: 0, compression_ratio: 0, data: '', success: false, error: error instanceof Error ? error.message : '压缩失败', format: '' }
          } : f
        ))
      }
    }
    setIsCompressing(false)
  }

  const handleDownload = (item: FileItem) => {
    if (item.result?.success && item.result.data) {
      const a = document.createElement('a')
      a.href = item.result.data
      const originalName = item.file.name.replace(/\.[^.]+$/, '')
      const ext = item.result.format === 'jpeg' ? 'jpg' : item.result.format
      a.download = `${originalName}.${ext}`
      a.click()
    }
  }

  const handleDownloadAll = async () => {
    const successItems = files.filter(f => f.result?.success && f.result.data)
    if (successItems.length === 1) {
      handleDownload(successItems[0])
    } else if (successItems.length > 1) {
      const zip = new JSZip()
      for (const item of successItems) {
        const base64Data = item.result!.data.split(',')[1]
        const originalName = item.file.name.replace(/\.[^.]+$/, '')
        const ext = item.result!.format === 'jpeg' ? 'jpg' : item.result!.format
        zip.file(`${originalName}.${ext}`, base64Data, { base64: true })
      }
      const blob = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `imglite_${Date.now()}.zip`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const handleCompare = (item: FileItem) => {
    if (item.result?.success && item.result.data) {
      setCompareData({ originalUrl: item.originalUrl, compressedUrl: item.result.data, filename: item.file.name })
    }
  }

  const handleClear = () => {
    progressIntervals.current.forEach(interval => clearInterval(interval))
    progressIntervals.current.clear()
    files.forEach(f => URL.revokeObjectURL(f.originalUrl))
    setFiles([])
  }

  const totalFiles = files.length
  const doneFiles = files.filter(f => f.status === 'done').length
  const totalOriginal = files.reduce((sum, f) => sum + f.file.size, 0)
  const totalCompressed = files.reduce((sum, f) => sum + (f.result?.compressed_size || 0), 0)
  const totalRatio = totalOriginal > 0 ? (1 - totalCompressed / totalOriginal) * 100 : 0
  const savedSize = totalOriginal - totalCompressed

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur-lg">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold">ImgLite</h1>
              <p className="text-xs text-muted-foreground">高效压缩 · 保持质量</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={toggleTheme} title={isDark ? '切换浅色' : '切换深色'}>
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button variant="ghost" size="icon" asChild>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer">
                <Github className="h-5 w-5" />
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      {files.length === 0 && (
        <section className="py-12 px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              让图片更轻，质量不变
            </h2>
            <p className="text-muted-foreground mb-6">
              支持 PNG、JPEG、WebP 格式，单次最多处理 20 张图片
            </p>
          </div>
        </section>
      )}

      {/* Main */}
      <main className="flex-1 max-w-5xl mx-auto px-4 py-6 space-y-6 w-full">
        {/* Format Selector */}
        <div className="flex items-center justify-center gap-3">
          <span className="text-sm text-muted-foreground">输出格式:</span>
          <ToggleGroup
            type="single"
            value={outputFormat}
            onValueChange={(value) => value && setOutputFormat(value as OutputFormat)}
            disabled={isCompressing}
            className="bg-muted p-1 rounded-lg"
          >
            {FORMAT_OPTIONS.map(option => (
              <ToggleGroupItem
                key={option.value}
                value={option.value}
                className="data-[state=on]:bg-background data-[state=on]:shadow-sm px-3 py-1.5 text-sm"
              >
                {option.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>

        <UploadZone onFilesSelected={handleFilesSelected} disabled={isCompressing} />

        {files.length > 0 && (
          <div className="space-y-4">
            {/* Summary Card */}
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">进度</p>
                      <p className="text-2xl font-bold">{doneFiles}<span className="text-muted-foreground text-lg">/{totalFiles}</span></p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">原始大小</p>
                      <p className="text-2xl font-bold">{formatSize(totalOriginal)}</p>
                    </div>
                    {doneFiles > 0 && (
                      <>
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">压缩后</p>
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{formatSize(totalCompressed)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">节省空间</p>
                          <div className="flex items-baseline gap-2">
                            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{totalRatio.toFixed(0)}%</p>
                            <span className="text-sm text-muted-foreground">({formatSize(savedSize)})</span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="flex gap-2">
                    {doneFiles > 0 && (
                      <Button onClick={handleDownloadAll} disabled={isCompressing}>
                        <Download className="mr-2 h-4 w-4" />
                        {doneFiles > 1 ? '下载全部' : '下载'}
                      </Button>
                    )}
                    <Button variant="outline" onClick={handleClear} disabled={isCompressing}>
                      清除
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Files Grid */}
            <div className="grid gap-2">
              {files.map((item) => (
                <Card key={item.id} className={cn(item.status === 'error' && 'border-destructive/50')}>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      {/* Thumbnail */}
                      <div className="w-12 h-12 rounded-lg overflow-hidden shrink-0 bg-muted relative">
                        <img
                          src={item.originalUrl}
                          alt={item.file.name}
                          className="w-full h-full object-cover"
                        />
                        {item.status === 'compressing' && (
                          <div className="absolute inset-0 bg-background/80 flex items-center justify-center">
                            <Loader2 className="w-5 h-5 text-primary animate-spin" />
                          </div>
                        )}
                        {item.status === 'error' && (
                          <div className="absolute inset-0 bg-destructive/20 flex items-center justify-center">
                            <XCircle className="w-5 h-5 text-destructive" />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-4">
                          <p className="font-medium truncate text-sm">{item.file.name}</p>
                          <span className="text-xs text-muted-foreground shrink-0">{formatSize(item.file.size)}</span>
                        </div>

                        {(item.status === 'pending' || item.status === 'compressing') && (
                          <div className="mt-2 flex items-center gap-3">
                            <Progress
                              value={item.progress}
                              className="flex-1"
                              indicatorClassName={cn(
                                item.status === 'error' && 'bg-destructive',
                                item.status === 'done' && 'bg-green-500'
                              )}
                            />
                            <span className="text-xs font-medium text-primary w-10 text-right">
                              {Math.round(item.progress)}%
                            </span>
                          </div>
                        )}

                        {item.status === 'done' && item.result && (
                          <div className="mt-1 flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground">{formatSize(item.result.original_size)}</span>
                            <span className="text-muted-foreground">→</span>
                            <span className="text-green-600 dark:text-green-400">{formatSize(item.result.compressed_size)}</span>
                            <span className="text-green-600 dark:text-green-400 font-medium">-{item.result.compression_ratio.toFixed(0)}%</span>
                            <span className="px-1.5 py-0.5 text-xs bg-muted rounded uppercase">{item.result.format}</span>
                          </div>
                        )}

                        {item.status === 'error' && item.result && (
                          <p className="text-xs text-destructive mt-1">{item.result.error}</p>
                        )}
                      </div>

                      {item.status === 'done' && item.result?.success && (
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => handleCompare(item)} title="对比效果">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDownload(item)} title="下载">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t py-4">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">
            ImgLite - 高效图片压缩工具
          </p>
        </div>
      </footer>

      {compareData && (
        <ImageCompare
          originalUrl={compareData.originalUrl}
          compressedUrl={compareData.compressedUrl}
          filename={compareData.filename}
          onClose={() => setCompareData(null)}
        />
      )}
    </div>
  )
}

export default App
