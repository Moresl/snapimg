import { cn } from '@/lib/utils'
import { Upload } from 'lucide-react'
import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from './ui/button'

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 
const MAX_FILES = 20
const ACCEPTED_TYPES = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/webp': ['.webp'],
}

export function UploadZone({ onFilesSelected, disabled }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFilesSelected(acceptedFiles)
    }
  }, [onFilesSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    maxFiles: MAX_FILES,
    disabled,
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200 bg-card",
        isDragActive
          ? "border-primary bg-primary/10"
          : "border-primary/50 hover:border-primary hover:bg-primary/5",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <input {...getInputProps()} />

      <div className="flex items-center justify-center gap-4">
        <div className={cn(
          "w-12 h-12 rounded-full flex items-center justify-center shrink-0",
          isDragActive ? "bg-primary/20" : "bg-muted"
        )}>
          <Upload className={cn("w-6 h-6", isDragActive ? "text-primary" : "text-muted-foreground")} />
        </div>

        <div className="text-left">
          <p className="font-medium text-foreground">
            {isDragActive ? '释放以上传' : '拖拽或点击上传图片'}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            PNG / JPEG / WebP · 最大 10MB · 最多 20 个
          </p>
        </div>

        <Button className="ml-auto" disabled={disabled}>
          选择文件
        </Button>
      </div>
    </div>
  )
}
