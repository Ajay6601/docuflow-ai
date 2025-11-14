import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, FileText, Loader2 } from 'lucide-react'
import { Document } from '../types/document'
import { documentApi } from '../services/api'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { formatBytes, formatDate } from '../lib/utils'

export const DocumentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [document, setDocument] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      loadDocument(parseInt(id))
    }
  }, [id])

  const loadDocument = async (docId: number) => {
    setLoading(true)
    try {
      const doc = await documentApi.get(docId)
      setDocument(doc)
    } catch (error) {
      console.error('Failed to load document:', error)
      alert('Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (document) {
      await documentApi.download(document.id, document.original_filename)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Document not found</p>
        <Button onClick={() => navigate('/')} className="mt-4">
          Go Back
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Documents
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{document.original_filename}</h1>
            <p className="text-gray-500">
              {formatBytes(document.file_size)} • {formatDate(document.created_at)}
            </p>
          </div>

          <Button onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary */}
          {document.summary && (
            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{document.summary}</p>
              </CardContent>
            </Card>
          )}

          {/* Extracted Data */}
          {document.extracted_data && Object.keys(document.extracted_data).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Extracted Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-3">
                  {Object.entries(document.extracted_data).map(([key, value]) => (
                    <div key={key} className="border-b pb-2 last:border-0">
                      <dt className="text-sm font-medium text-gray-500 capitalize">
                        {key.replace(/_/g, ' ')}
                      </dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          )}

          {/* Extracted Text */}
          {document.extracted_text && (
            <Card>
              <CardHeader>
                <CardTitle>Extracted Text</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                  <pre className="text-sm whitespace-pre-wrap font-mono">
                    {document.extracted_text}
                  </pre>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status */}
          <Card>
            <CardHeader>
              <CardTitle>Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-500 mb-1">Processing Status</p>
                <Badge variant={document.status === 'completed' ? 'success' : 'warning'}>
                  {document.status}
                </Badge>
              </div>

              <div>
                <p className="text-sm text-gray-500 mb-1">Document Type</p>
                <Badge>{document.document_type}</Badge>
                {document.document_type_confidence && (
                  <p className="text-xs text-gray-500 mt-1">
                    {(document.document_type_confidence * 100).toFixed(0)}% confident
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {document.page_count && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Pages</span>
                  <span className="font-medium">{document.page_count}</span>
                </div>
              )}

              {document.extraction_method && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Extraction Method</span>
                  <span className="font-medium">{document.extraction_method}</span>
                </div>
              )}

              {document.processing_time && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Processing Time</span>
                  <span className="font-medium">{document.processing_time.toFixed(2)}s</span>
                </div>
              )}

              {document.ai_processing_cost && (
                <div className="flex justify-between">
                  <span className="text-gray-500">AI Cost</span>
                  <span className="font-medium">${document.ai_processing_cost.toFixed(4)}</span>
                </div>
              )}

              <div className="flex justify-between">
                <span className="text-gray-500">File Type</span>
                <span className="font-medium">{document.file_type}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="font-medium">{formatDate(document.created_at)}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-500">Updated</span>
                <span className="font-medium">{formatDate(document.updated_at)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}