import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
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
      className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
        transition-all duration-200
        ${isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50 hover:bg-muted/30'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />

      <div className="flex items-center justify-center gap-4">
        <div className={`
          w-12 h-12 rounded-full flex items-center justify-center shrink-0
          ${isDragActive ? 'bg-primary/20' : 'bg-muted'}
        `}>
          <Upload className={`w-6 h-6 ${isDragActive ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>

        <div className="text-left">
          <p className="font-medium">
            {isDragActive ? '释放以上传' : '拖拽或点击上传图片'}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            PNG / JPEG / WebP · 最大 10MB · 最多 20 个
          </p>
        </div>

        <button
          type="button"
          className="btn-primary ml-auto"
          disabled={disabled}
        >
          选择文件
        </button>
      </div>
    </div>
  )
}
