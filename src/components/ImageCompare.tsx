import { X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Button } from './ui/button'

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
      <div className="fixed inset-0 z-50 bg-muted flex items-center justify-center">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  const clipPath = `inset(0 ${100 - sliderPosition}% 0 0)`
  const sliderLeftPx = imageOffset.left + (sliderPosition / 100) * imageSize.width

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 bg-muted cursor-ew-resize select-none"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
    >
      <Button
        variant="secondary"
        size="icon"
        className="absolute top-4 right-4 z-20 rounded-full shadow-md"
        onClick={onClose}
      >
        <X className="h-5 w-5" />
      </Button>
      <div className="absolute top-4 left-4 z-20">
        <p className="font-medium text-foreground">{filename}</p>
        <p className="text-sm text-muted-foreground">拖动滑块对比压缩效果</p>
      </div>
      <div
        className="absolute bottom-6 z-20 px-3 py-1.5 rounded-full bg-background shadow text-foreground text-sm font-medium"
        style={{ left: imageOffset.left + imageSize.width * 0.25, transform: 'translateX(-50%)' }}
      >
        原图
      </div>
      <div
        className="absolute bottom-6 z-20 px-3 py-1.5 rounded-full bg-background shadow text-foreground text-sm font-medium"
        style={{ left: imageOffset.left + imageSize.width * 0.75, transform: 'translateX(-50%)' }}
      >
        压缩后
      </div>
      <div
        className="absolute"
        style={{
          left: imageOffset.left,
          top: imageOffset.top,
          width: imageSize.width,
          height: imageSize.height
        }}
      >
        <img
          src={compressedUrl}
          alt="压缩后"
          className="absolute top-0 left-0 rounded-lg shadow-lg"
          style={{ width: imageSize.width, height: imageSize.height }}
          draggable={false}
        />

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

      <div
        className="absolute top-0 bottom-0 w-0.5 bg-foreground pointer-events-none z-10"
        style={{ left: sliderLeftPx, transform: 'translateX(-50%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-background shadow-lg border-2 border-foreground flex items-center justify-center cursor-ew-resize pointer-events-auto">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-foreground">
            <path d="M8 12L4 8M4 8L8 4M4 8H12M16 12L20 16M20 16L16 20M20 16H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  )
}
