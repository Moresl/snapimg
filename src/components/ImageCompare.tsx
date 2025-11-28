import { useState, useRef, useEffect } from 'react'
import { X } from 'lucide-react'

interface ImageCompareProps {
  originalUrl: string
  compressedUrl: string
  filename: string
  onClose: () => void
}

export function ImageCompare({ originalUrl, compressedUrl, filename, onClose }: ImageCompareProps) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)

  // 加载图片获取尺寸
  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      const maxWidth = window.innerWidth * 0.9
      const maxHeight = window.innerHeight * 0.8

      let width = img.naturalWidth
      let height = img.naturalHeight

      if (width > maxWidth) {
        height = (maxWidth / width) * height
        width = maxWidth
      }
      if (height > maxHeight) {
        width = (maxHeight / height) * width
        height = maxHeight
      }

      setImageSize({ width, height })
    }
    img.src = originalUrl
  }, [originalUrl])

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = clientX - rect.left
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
    setSliderPosition(percentage)
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true
    handleMove(e.clientX)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging.current) {
      handleMove(e.clientX)
    }
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    handleMove(e.touches[0].clientX)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    handleMove(e.touches[0].clientX)
  }

  useEffect(() => {
    const handleMouseUp = () => {
      isDragging.current = false
    }
    window.addEventListener('mouseup', handleMouseUp)
    return () => window.removeEventListener('mouseup', handleMouseUp)
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (imageSize.width === 0) {
    return (
      <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    )
  }

  const clipPath = `inset(0 ${100 - sliderPosition}% 0 0)`

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
      {/* Close button */}
      <button
        className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
        onClick={onClose}
      >
        <X className="w-6 h-6" />
      </button>

      {/* Title */}
      <div className="absolute top-4 left-4 z-10 text-white">
        <p className="font-medium">{filename}</p>
        <p className="text-sm text-white/60">拖动滑块对比压缩效果</p>
      </div>

      {/* Labels */}
      <div className="absolute bottom-6 left-1/4 -translate-x-1/2 z-10 px-3 py-1.5 rounded-full bg-black/70 text-white text-sm font-medium">
        原图
      </div>
      <div className="absolute bottom-6 right-1/4 translate-x-1/2 z-10 px-3 py-1.5 rounded-full bg-black/70 text-white text-sm font-medium">
        压缩后
      </div>

      {/* Compare container */}
      <div
        ref={containerRef}
        className="relative cursor-ew-resize select-none"
        style={{ width: imageSize.width, height: imageSize.height }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
      >
        {/* Compressed image (底层，完整显示) */}
        <img
          src={compressedUrl}
          alt="压缩后"
          className="absolute top-0 left-0"
          style={{ width: imageSize.width, height: imageSize.height }}
          draggable={false}
        />

        {/* Original image (上层，用 clip-path 裁剪) */}
        <img
          src={originalUrl}
          alt="原始"
          className="absolute top-0 left-0"
          style={{
            width: imageSize.width,
            height: imageSize.height,
            clipPath: clipPath
          }}
          draggable={false}
        />

        {/* Slider line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white pointer-events-none"
          style={{ left: `${sliderPosition}%`, transform: 'translateX(-50%)' }}
        >
          {/* Slider handle */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white shadow-xl flex items-center justify-center cursor-ew-resize pointer-events-auto">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-gray-600">
              <path d="M8 12L4 8M4 8L8 4M4 8H12M16 12L20 16M20 16L16 20M20 16H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  )
}
