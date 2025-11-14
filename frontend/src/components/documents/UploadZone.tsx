import React, { useCallback, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { Button } from '../ui/Button'
import { documentApi } from '../../services/api'
import { formatBytes } from '../../lib/utils'

interface UploadZoneProps {
  onUploadSuccess?: () => void
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    setFiles((prev) => [...prev, ...droppedFiles])
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...selectedFiles])
    }
  }, [])

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleUpload = async () => {
    if (files.length === 0) return
    
    setUploading(true)
    
    try {
      for (const file of files) {
        setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }))
        
        await documentApi.upload(file, true)
        
        setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }))
      }
      
      // Clear files after successful upload
      setFiles([])
      setUploadProgress({})
      
      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary'}
        `}
      >
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
        />
        
        <label htmlFor="file-upload" className="cursor-pointer">
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-700 mb-2">
            Drop files here or click to upload
          </p>
          <p className="text-sm text-gray-500">
            Supports PDF, PNG, JPG, DOCX, XLSX (max 50MB)
          </p>
        </label>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium">Selected Files ({files.length})</h3>
          
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1">
                  <FileText className="h-5 w-5 text-gray-500" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
                  </div>
                </div>
                
                {uploadProgress[file.name] !== undefined ? (
                  <div className="text-sm text-green-600 font-medium">
                    {uploadProgress[file.name]}%
                  </div>
                ) : (
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 hover:bg-gray-200 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <Button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full"
          >
            {uploading ? 'Uploading...' : `Upload ${files.length} file(s)`}
          </Button>
        </div>
      )}
    </div>
  )
}