import { X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface ImageCompareProps {
  originalUrl: string
  compressedUrl: string
  filename: string
  onClose: () => void
}

export function ImageCompare({ originalUrl, compressedUrl, filename, onClose }: ImageCompareProps) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 })
  const [imageOffset, setImageOffset] = useState({ left: 0, top: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)

  // 加载图片获取尺寸
  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      const maxWidth = window.innerWidth * 0.8
      const maxHeight = window.innerHeight * 0.7

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
      setImageOffset({
        left: (window.innerWidth - width) / 2,
        top: (window.innerHeight - height) / 2
      })
    }
    img.src = originalUrl
  }, [originalUrl])

  const handleMove = (clientX: number) => {
    // 限制滑块在图片范围内
    const minX = imageOffset.left
    const maxX = imageOffset.left + imageSize.width
    const clampedX = Math.max(minX, Math.min(maxX, clientX))
    const percentage = ((clampedX - minX) / imageSize.width) * 100
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
    isDragging.current = true
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
      <div className="fixed inset-0 z-50 bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
        <div className="text-neutral-600 dark:text-neutral-300">加载中...</div>
      </div>
    )
  }

  // 计算裁剪：基于滑块位置裁剪图片
  const clipPath = `inset(0 ${100 - sliderPosition}% 0 0)`

  // 滑块在屏幕上的实际位置
  const sliderLeftPx = imageOffset.left + (sliderPosition / 100) * imageSize.width

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 bg-neutral-100 dark:bg-neutral-800 cursor-ew-resize select-none"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
    >
      {/* Close button */}
      <button
        className="absolute top-4 right-4 z-20 w-10 h-10 rounded-full bg-white dark:bg-neutral-700 shadow-md hover:bg-neutral-50 dark:hover:bg-neutral-600 flex items-center justify-center text-neutral-600 dark:text-neutral-300 transition-colors"
        onClick={onClose}
      >
        <X className="w-5 h-5" />
      </button>

      {/* Title */}
      <div className="absolute top-4 left-4 z-20">
        <p className="font-medium text-neutral-800 dark:text-neutral-200">{filename}</p>
        <p className="text-sm text-neutral-500 dark:text-neutral-400">拖动滑块对比压缩效果</p>
      </div>

      {/* Labels */}
      <div className="absolute bottom-6 z-20 px-3 py-1.5 rounded-full bg-white dark:bg-neutral-700 shadow text-neutral-700 dark:text-neutral-200 text-sm font-medium"
        style={{ left: imageOffset.left + imageSize.width * 0.25, transform: 'translateX(-50%)' }}>
        原图
      </div>
      <div className="absolute bottom-6 z-20 px-3 py-1.5 rounded-full bg-white dark:bg-neutral-700 shadow text-neutral-700 dark:text-neutral-200 text-sm font-medium"
        style={{ left: imageOffset.left + imageSize.width * 0.75, transform: 'translateX(-50%)' }}>
        压缩后
      </div>

      {/* Image container - centered */}
      <div
        className="absolute"
        style={{
          left: imageOffset.left,
          top: imageOffset.top,
          width: imageSize.width,
          height: imageSize.height
        }}
      >
        {/* Compressed image (底层，完整显示) */}
        <img
          src={compressedUrl}
          alt="压缩后"
          className="absolute top-0 left-0 rounded-lg shadow-lg"
          style={{ width: imageSize.width, height: imageSize.height }}
          draggable={false}
        />

        {/* Original image (上层，用 clip-path 裁剪) */}
        <img
          src={originalUrl}
          alt="原始"
          className="absolute top-0 left-0 rounded-lg shadow-lg"
          style={{
            width: imageSize.width,
            height: imageSize.height,
            clipPath: clipPath
          }}
          draggable={false}
        />
      </div>

      {/* Slider line - 全屏高度，但限制在图片水平范围内 */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-black dark:bg-white pointer-events-none z-10"
        style={{ left: sliderLeftPx, transform: 'translateX(-50%)' }}
      >
        {/* Slider handle */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white shadow-lg border-2 border-black dark:border-white flex items-center justify-center cursor-ew-resize pointer-events-auto">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M8 12L4 8M4 8L8 4M4 8H12M16 12L20 16M20 16L16 20M20 16H12" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  )
}
