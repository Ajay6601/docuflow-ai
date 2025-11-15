import React from 'react'
import { Download } from 'lucide-react'
import { Button } from '../ui/Button'

interface ExportButtonProps {
  data: any
  filename: string
}

export const ExportButton: React.FC<ExportButtonProps> = ({ data, filename }) => {
  const handleExport = () => {
    const jsonStr = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <Button variant="outline" size="sm" onClick={handleExport}>
      <Download className="h-4 w-4 mr-2" />
      Export Data
    </Button>
  )
}