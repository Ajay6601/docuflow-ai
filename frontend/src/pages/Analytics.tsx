import React, { useEffect, useState } from 'react'
import { 
  FileText, 
  TrendingUp, 
  Clock, 
  DollarSign, 
  CheckCircle,
  XCircle,
  Loader2,
  HardDrive,
  Calendar
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { StatCard } from '../components/analytics/StatCard'
import { analyticsApi } from '../services/api'
import { formatBytes } from '../lib/utils'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

export const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<any>(null)
  const [documentTypes, setDocumentTypes] = useState<any[]>([])
  const [uploadTimeline, setUploadTimeline] = useState<any[]>([])
  const [processingStats, setProcessingStats] = useState<any[]>([])
  const [costTracking, setCostTracking] = useState<any[]>([])
  const [extractionMethods, setExtractionMethods] = useState<any[]>([])
  const [timeRange, setTimeRange] = useState(7)

  useEffect(() => {
    loadAnalytics()
  }, [timeRange])

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      const [
        overviewData,
        typesData,
        timelineData,
        statsData,
        costData,
        methodsData,
      ] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getDocumentTypes(),
        analyticsApi.getUploadTimeline(timeRange),
        analyticsApi.getProcessingStats(timeRange),
        analyticsApi.getCostTracking(timeRange),
        analyticsApi.getExtractionMethods(),
      ])

      setOverview(overviewData)
      setDocumentTypes(typesData)
      setUploadTimeline(timelineData)
      setProcessingStats(statsData)
      setCostTracking(costData)
      setExtractionMethods(methodsData)
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const successRate = overview?.total_documents > 0
    ? ((overview.status_counts.completed / overview.total_documents) * 100).toFixed(1)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your document processing</p>
        </div>

        {/* Time Range Selector */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-4 py-2 border rounded-lg"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Documents"
          value={overview?.total_documents || 0}
          icon={FileText}
          description={`${overview?.uploaded_this_month || 0} this month`}
        />

        <StatCard
          title="Success Rate"
          value={`${successRate}%`}
          icon={CheckCircle}
          description={`${overview?.status_counts.completed || 0} completed`}
        />

        <StatCard
          title="Avg Processing Time"
          value={`${overview?.average_processing_time || 0}s`}
          icon={Clock}
          description="Per document"
        />

        <StatCard
          title="Total AI Cost"
          value={`$${overview?.total_ai_cost?.toFixed(4) || '0.0000'}`}
          icon={DollarSign}
          description="OpenAI API usage"
        />
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Uploaded Today"
          value={overview?.uploaded_today || 0}
          icon={Calendar}
        />

        <StatCard
          title="Uploaded This Week"
          value={overview?.uploaded_this_week || 0}
          icon={TrendingUp}
        />

        <StatCard
          title="Storage Used"
          value={formatBytes(overview?.total_storage_bytes || 0)}
          icon={HardDrive}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Types */}
        <Card>
          <CardHeader>
            <CardTitle>Document Types Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={documentTypes}
                  dataKey="count"
                  nameKey="type"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.type}: ${entry.count}`}
                >
                  {documentTypes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Status Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { status: 'Uploaded', count: overview?.status_counts.uploaded || 0 },
                  { status: 'Processing', count: overview?.status_counts.processing || 0 },
                  { status: 'Completed', count: overview?.status_counts.completed || 0 },
                  { status: 'Failed', count: overview?.status_counts.failed || 0 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6">
        {/* Upload Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={uploadTimeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Documents Uploaded"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Processing Time Trends */}
        {processingStats.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Average Processing Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={processingStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="avg_processing_time" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Avg Time (seconds)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Cost Tracking */}
        {costTracking.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>AI Processing Costs</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={costTracking}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="cost" fill="#f59e0b" name="Daily Cost ($)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Extraction Methods */}
      {extractionMethods.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Extraction Methods Used</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={extractionMethods} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="method" type="category" />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}