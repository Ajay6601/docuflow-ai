import React, { useState } from 'react'
import { 
  FileText, 
  Upload as UploadIcon, 
  Search as SearchIcon, 
  LogOut, 
  User as UserIcon,
  BarChart3  // NEW
} from 'lucide-react'
import { UploadZone } from '../components/documents/UploadZone'
import { DocumentList } from '../components/documents/DocumentList'
import { SearchBar } from '../components/documents/SearchBar'
import { Analytics } from './Analytics'  // NEW
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { useWebSocket } from '../hooks/useWebSocket'
// import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authSore'
export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'documents' | 'upload' | 'search' | 'analytics'>('documents')  // UPDATED
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const { isConnected, messages } = useWebSocket()

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1)
    setActiveTab('documents')
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  React.useEffect(() => {
    const lastMessage = messages[messages.length - 1]
    if (lastMessage && lastMessage.type === 'document_status') {
      if (lastMessage.status === 'completed' || lastMessage.status === 'failed') {
        setRefreshTrigger(prev => prev + 1)
      }
    }
  }, [messages])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary rounded-lg">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">DocuFlow AI</h1>
                <p className="text-sm text-gray-500">Enterprise Document Intelligence</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* WebSocket Status */}
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="p-2 bg-primary/10 rounded-full">
                    <UserIcon className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
                    <Badge variant="outline" className="text-xs">{user?.role}</Badge>
                  </div>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-1 z-50">
                    <div className="px-4 py-2 border-b">
                      <p className="text-sm font-medium">{user?.username}</p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-600"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('documents')}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${activeTab === 'documents' 
                ? 'bg-primary text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }
            `}
          >
            <FileText className="h-4 w-4" />
            Documents
          </button>

          <button
            onClick={() => setActiveTab('upload')}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${activeTab === 'upload' 
                ? 'bg-primary text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }
            `}
          >
            <UploadIcon className="h-4 w-4" />
            Upload
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${activeTab === 'search' 
                ? 'bg-primary text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }
            `}
          >
            <SearchIcon className="h-4 w-4" />
            Search
          </button>

          {/* NEW - Analytics Tab */}
          <button
            onClick={() => setActiveTab('analytics')}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${activeTab === 'analytics' 
                ? 'bg-primary text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }
            `}
          >
            <BarChart3 className="h-4 w-4" />
            Analytics
          </button>
        </div>

        {/* Content */}
        <div>
          {activeTab === 'documents' && (
            <Card>
              <CardHeader>
                <CardTitle>My Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentList refreshTrigger={refreshTrigger} />
              </CardContent>
            </Card>
          )}

          {activeTab === 'upload' && (
            <Card>
              <CardHeader>
                <CardTitle>Upload Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <UploadZone onUploadSuccess={handleUploadSuccess} />
              </CardContent>
            </Card>
          )}

          {activeTab === 'search' && (
            <Card>
              <CardHeader>
                <CardTitle>Search Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <SearchBar />
              </CardContent>
            </Card>
          )}

          {/* NEW - Analytics Content */}
          {activeTab === 'analytics' && <Analytics />}
        </div>

        {/* Recent Activity */}
        {messages.length > 0 && activeTab !== 'analytics' && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {messages.slice(-5).reverse().map((msg, index) => (
                  <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                    {msg.type === 'document_status' && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">Document {msg.document_id}:</span>
                        <span>{msg.message}</span>
                        {msg.progress !== undefined && (
                          <span className="text-gray-500">({msg.progress}%)</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}