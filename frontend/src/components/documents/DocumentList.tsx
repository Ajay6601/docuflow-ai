import React, { useEffect, useState } from 'react'
import { FileText, Download, Trash2, RefreshCw, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import type { Document } from '../../types/document'
import { DocumentStatus } from '../../types/document'
import { documentApi } from '../../services/api'
import { formatBytes, formatDate, cn } from '../../lib/utils'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { Card, CardContent } from '../ui/Card'

interface DocumentListProps {
  refreshTrigger?: number
}

export const DocumentList: React.FC<DocumentListProps> = ({ refreshTrigger }) => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [selectedStatus, setSelectedStatus] = useState<string>('')

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const response = await documentApi.list(page, 20, selectedStatus || undefined)
      setDocuments(response.items)
      setTotal(response.total)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [page, selectedStatus, refreshTrigger])

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return
    
    try {
      await documentApi.delete(id)
      loadDocuments()
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document')
    }
  }

  const handleDownload = async (doc: Document) => {
    try {
      await documentApi.download(doc.id, doc.original_filename)
    } catch (error) {
      console.error('Failed to download document:', error)
      alert('Failed to download document')
    }
  }

  const handleReprocess = async (id: number) => {
    try {
      await documentApi.reprocess(id)
      loadDocuments()
    } catch (error) {
      console.error('Failed to reprocess document:', error)
      alert('Failed to reprocess document')
    }
  }

  const getStatusBadge = (status: DocumentStatus) => {
    switch (status) {
      case DocumentStatus.COMPLETED:
        return <Badge variant="success" className="flex items-center gap-1">
          <CheckCircle className="h-3 w-3" /> Completed
        </Badge>
      case DocumentStatus.PROCESSING:
        return <Badge variant="warning" className="flex items-center gap-1">
          <Loader2 className="h-3 w-3 animate-spin" /> Processing
        </Badge>
      case DocumentStatus.FAILED:
        return <Badge variant="destructive" className="flex items-center gap-1">
          <XCircle className="h-3 w-3" /> Failed
        </Badge>
      default:
        return <Badge variant="secondary" className="flex items-center gap-1">
          <Clock className="h-3 w-3" /> Uploaded
        </Badge>
    }
  }

  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      invoice: 'bg-blue-100 text-blue-800',
      contract: 'bg-purple-100 text-purple-800',
      resume: 'bg-green-100 text-green-800',
      receipt: 'bg-orange-100 text-orange-800',
      form: 'bg-pink-100 text-pink-800',
      letter: 'bg-indigo-100 text-indigo-800',
      report: 'bg-cyan-100 text-cyan-800',
      other: 'bg-gray-100 text-gray-800',
    }
    return colors[type] || colors.other
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="">All Status</option>
          <option value="uploaded">Uploaded</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>

        <div className="flex-1" />

        <Button variant="outline" size="sm" onClick={loadDocuments}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Document List */}
      <div className="space-y-3">
        {documents.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No documents found</p>
            </CardContent>
          </Card>
        ) : (
          documents.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <FileText className="h-6 w-6 text-primary" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-lg truncate">
                          {doc.original_filename}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {formatBytes(doc.file_size)} • {formatDate(doc.created_at)}
                        </p>
                      </div>
                      
                      <div className="flex gap-2">
                        {getStatusBadge(doc.status)}
                        {doc.document_type !== 'unknown' && (
                          <Badge className={getDocumentTypeColor(doc.document_type)}>
                            {doc.document_type}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Summary */}
                    {doc.summary && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {doc.summary}
                      </p>
                    )}

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
                      {doc.page_count && (
                        <span>{doc.page_count} pages</span>
                      )}
                      {doc.extraction_method && (
                        <span>• {doc.extraction_method}</span>
                      )}
                      {doc.processing_time && (
                        <span>• {doc.processing_time.toFixed(2)}s</span>
                      )}
                      {doc.ai_processing_cost && (
                        <span>• ${doc.ai_processing_cost.toFixed(4)}</span>
                      )}
                      {doc.document_type_confidence && (
                        <span>• {(doc.document_type_confidence * 100).toFixed(0)}% confident</span>
                      )}
                    </div>

                    {/* Error Message */}
                    {doc.extraction_error && (
                      <div className="bg-red-50 border border-red-200 rounded p-2 mb-3">
                        <p className="text-sm text-red-800">{doc.extraction_error}</p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownload(doc)}
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </Button>

                      {doc.status === DocumentStatus.FAILED && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReprocess(doc.id)}
                        >
                          <RefreshCw className="h-4 w-4 mr-1" />
                          Retry
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(`/documents/${doc.id}`, '_blank')}
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        View
                      </Button>

                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDelete(doc.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} documents
          </p>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => p + 1)}
              disabled={page * 20 >= total}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}