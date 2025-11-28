import JSZip from 'jszip'
import { Download, Eye, Github, Loader2, Moon, Sun, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ImageCompare } from './components/ImageCompare'
import { UploadZone } from './components/UploadZone'
import { compressSingleImage, formatSize, type CompressResult, type OutputFormat } from './lib/api'

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

// 进度条组件
function ProgressBar({ progress, status }: { progress: number; status: FileStatus }) {
  return (
    <div className="mt-2 flex items-center gap-3">
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            status === 'error' ? 'bg-destructive' :
            status === 'done' ? 'bg-success' :
            'bg-gradient-to-r from-primary to-primary/60'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <span className={`text-xs font-bold w-12 text-right ${
        status === 'error' ? 'text-destructive' :
        status === 'done' ? 'text-success' :
        'text-primary'
      }`}>
        {Math.round(progress)}%
      </span>
    </div>
  )
}

const FORMAT_OPTIONS: { value: OutputFormat; label: string; desc: string }[] = [
  { value: 'original', label: '保持原格式', desc: '不转换格式' },
  { value: 'webp', label: 'WebP', desc: '压缩率最高' },
  { value: 'png', label: 'PNG', desc: '无损透明' },
  { value: 'jpeg', label: 'JPEG', desc: '照片最佳' },
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
      // 使用实际输出格式的扩展名
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
      a.download = `compressed_images_${Date.now()}.zip`
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
      <header className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur-lg">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg width="36" height="36" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="32" height="32" rx="8" className="fill-primary"/>
              <rect x="6" y="8" width="14" height="12" rx="2" fill="white" opacity="0.9"/>
              <circle cx="10" cy="12" r="1.5" className="fill-primary"/>
              <path d="M6 17 L11 14 L14 16 L20 11" className="stroke-primary" strokeWidth="1.5" fill="none"/>
              <path d="M22 16 L26 20 M26 16 L22 20" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <path d="M19 22 L26 22 L26 25 L19 25 Z" fill="white" opacity="0.7"/>
            </svg>
            <div>
              <h1 className="text-xl font-bold">图片压缩</h1>
              <p className="text-xs text-muted-foreground">高效压缩 · 保持质量</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="btn-ghost btn-icon" title={isDark ? '切换浅色' : '切换深色'}>
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <a href="https://github.com/Moresl/ImageMinify" target="_blank" rel="noopener noreferrer" className="btn-ghost btn-icon">
              <Github className="w-5 h-5" />
            </a>
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
        <div className="flex items-center justify-center gap-2">
          <span className="text-sm text-muted-foreground">输出格式:</span>
          <div className="flex gap-1 p-1 bg-muted rounded-lg">
            {FORMAT_OPTIONS.map(option => (
              <button
                key={option.value}
                onClick={() => setOutputFormat(option.value)}
                disabled={isCompressing}
                className={`px-3 py-1.5 text-sm rounded-md transition-all ${
                  outputFormat === option.value
                    ? 'bg-background text-foreground shadow-sm font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                } ${isCompressing ? 'opacity-50 cursor-not-allowed' : ''}`}
                title={option.desc}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <UploadZone onFilesSelected={handleFilesSelected} disabled={isCompressing} />

        {files.length > 0 && (
          <div className="space-y-4">
            {/* Summary Card */}
            <div className="card overflow-hidden">
              <div className="card-content p-6">
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
                          <p className="text-2xl font-bold text-success">{formatSize(totalCompressed)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">节省空间</p>
                          <div className="flex items-baseline gap-2">
                            <p className="text-2xl font-bold text-success">{totalRatio.toFixed(0)}%</p>
                            <span className="text-sm text-muted-foreground">({formatSize(savedSize)})</span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="flex gap-2">
                    {doneFiles > 0 && (
                      <button className="btn-primary btn-lg gap-2" onClick={handleDownloadAll} disabled={isCompressing}>
                        <Download className="w-4 h-4" />
                        {doneFiles > 1 ? '下载全部' : '下载'}
                      </button>
                    )}
                    <button className="btn-outline btn-lg" onClick={handleClear} disabled={isCompressing}>
                      清除
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Files Grid */}
            <div className="grid gap-2">
              {files.map((item) => (
                <div
                  key={item.id}
                  className={`card ${item.status === 'error' ? 'border-destructive/50' : ''}`}
                >
                  <div className="card-content p-3">
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
                          <ProgressBar progress={item.progress} status={item.status} />
                        )}

                        {item.status === 'done' && item.result && (
                          <div className="mt-1 flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground">{formatSize(item.result.original_size)}</span>
                            <span className="text-muted-foreground">→</span>
                            <span className="text-success">{formatSize(item.result.compressed_size)}</span>
                            <span className="text-success font-medium">-{item.result.compression_ratio.toFixed(0)}%</span>
                            <span className="px-1.5 py-0.5 text-xs bg-muted rounded uppercase">{item.result.format}</span>
                          </div>
                        )}

                        {item.status === 'error' && item.result && (
                          <p className="text-xs text-destructive mt-1">{item.result.error}</p>
                        )}
                      </div>

                      {item.status === 'done' && item.result?.success && (
                        <div className="flex gap-1">
                          <button className="btn-ghost btn-icon" onClick={() => handleCompare(item)} title="对比效果">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="btn-ghost btn-icon" onClick={() => handleDownload(item)} title="下载">
                            <Download className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t py-4">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">
            图片压缩工具 ·{' '}
            <a href="https://github.com/Moresl/ImageMinify" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              GitHub
            </a>
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
