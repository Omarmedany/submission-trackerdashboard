import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Users, FileText, CheckCircle, XCircle, AlertTriangle, TrendingUp, Search } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

const AdminDashboard = ({ user }) => {
  const [analytics, setAnalytics] = useState(null)
  const [submissions, setSubmissions] = useState([])
  const [users, setUsers] = useState([])
  const [rejectionData, setRejectionData] = useState([])
  const [trendData, setTrendData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterTaskType, setFilterTaskType] = useState('all')

  useEffect(() => {
    fetchAdminData()
  }, [])

  const fetchAdminData = async () => {
    try {
      setLoading(true)
      
      // Fetch summary analytics
      const analyticsResponse = await fetch('/api/analytics/summary', {
        credentials: 'include',
      })
      
      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json()
        setAnalytics(analyticsData)
      }

      // Fetch all submissions
      const submissionsResponse = await fetch('/api/submissions', {
        credentials: 'include',
      })
      
      if (submissionsResponse.ok) {
        const submissionsData = await submissionsResponse.json()
        setSubmissions(submissionsData)
      }

      // Fetch users
      const usersResponse = await fetch('/api/users', {
        credentials: 'include',
      })
      
      if (usersResponse.ok) {
        const usersData = await usersResponse.json()
        setUsers(usersData)
      }

      // Fetch rejection by task type
      const rejectionResponse = await fetch('/api/analytics/charts/rejection-by-task-type', {
        credentials: 'include',
      })
      
      if (rejectionResponse.ok) {
        const rejectionChartData = await rejectionResponse.json()
        setRejectionData(rejectionChartData)
      }

      // Fetch submission trend
      const trendResponse = await fetch('/api/analytics/charts/submission-trend', {
        credentials: 'include',
      })
      
      if (trendResponse.ok) {
        const trendChartData = await trendResponse.json()
        setTrendData(trendChartData)
      }

    } catch (err) {
      setError('Failed to load admin dashboard data')
      console.error('Error fetching admin data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Filter submissions based on search and filters
  const filteredSubmissions = submissions.filter(submission => {
    const matchesSearch = !searchTerm || 
      (submission.Name && submission.Name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (submission['Task Type'] && submission['Task Type'].toLowerCase().includes(searchTerm.toLowerCase())) ||
      (submission['Miner/ Slicer Name'] && submission['Miner/ Slicer Name'].toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesStatus = filterStatus === 'all' || 
      submission['Is this rejected (Slice / Miner)'] === filterStatus

    const matchesTaskType = filterTaskType === 'all' || 
      submission['Task Type'] === filterTaskType

    return matchesSearch && matchesStatus && matchesTaskType
  })

  // Get unique task types for filter
  const taskTypes = [...new Set(submissions.map(s => s['Task Type']).filter(Boolean))]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Admin Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500 bg-gradient-to-r from-blue-50 to-blue-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Total Team Members</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-800">{analytics?.unique_members || 0}</div>
            <p className="text-xs text-blue-600">
              Active reviewers
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-indigo-500 bg-gradient-to-r from-indigo-50 to-indigo-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-indigo-700">Total Submissions</CardTitle>
            <FileText className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-800">{analytics?.total_submissions || 0}</div>
            <p className="text-xs text-indigo-600">
              All time submissions
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500 bg-gradient-to-r from-green-50 to-green-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Acceptance Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-800">
              {analytics?.total_submissions > 0 
                ? Math.round((analytics.accepted_count / analytics.total_submissions) * 100)
                : 0}%
            </div>
            <p className="text-xs text-green-600">
              {analytics?.accepted_count || 0} accepted / {analytics?.rejected_count || 0} rejected
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500 bg-gradient-to-r from-orange-50 to-orange-100">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">Tasks Changed</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-800">{analytics?.changed_count || 0}</div>
            <p className="text-xs text-orange-600">
              Modified by leaders
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Key Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-l-4 border-l-red-500 bg-gradient-to-r from-red-50 to-red-100">
          <CardHeader>
            <CardTitle className="text-lg text-red-700">Most Common Mistake</CardTitle>
            <CardDescription className="text-red-600">
              Primary reason for reviewer errors
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-semibold text-red-800">
              {analytics?.most_common_mistake || 'No data available'}
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500 bg-gradient-to-r from-amber-50 to-amber-100">
          <CardHeader>
            <CardTitle className="text-lg text-amber-700">Reviewer with Most Rejections</CardTitle>
            <CardDescription className="text-amber-600">
              Team member needing additional support
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-semibold text-amber-800">
              {analytics?.reviewer_with_most_rejected || 'No data available'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Data Tables */}
      <Tabs defaultValue="charts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="charts">Analytics Charts</TabsTrigger>
          <TabsTrigger value="submissions">All Submissions</TabsTrigger>
          <TabsTrigger value="users">Team Members</TabsTrigger>
        </TabsList>

        <TabsContent value="charts" className="space-y-6">
          {/* Rejection Rate by Task Type */}
          <Card>
            <CardHeader>
              <CardTitle>Rejection Rate by Task Type</CardTitle>
              <CardDescription>
                Performance breakdown across different task categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              {rejectionData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rejectionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="task_type" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="accepted" fill="#10b981" name="Accepted" />
                      <Bar dataKey="rejected" fill="#ef4444" name="Rejected" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No chart data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Submission Trend */}
          <Card>
            <CardHeader>
              <CardTitle>Submission Trend Over Time</CardTitle>
              <CardDescription>
                Daily submission volume tracking
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trendData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} name="Submissions" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No trend data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="submissions" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Filter Submissions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name, task type..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="Accepted">Accepted</SelectItem>
                    <SelectItem value="Rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filterTaskType} onValueChange={setFilterTaskType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by task type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Task Types</SelectItem>
                    {taskTypes.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Submissions Table */}
          <Card>
            <CardHeader>
              <CardTitle>All Submissions ({filteredSubmissions.length})</CardTitle>
              <CardDescription>
                Complete list of team submissions with filtering
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filteredSubmissions.length > 0 ? (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {filteredSubmissions.map((submission, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <div className="font-medium">{submission.Name || 'Unknown'}</div>
                          <div className="text-sm text-muted-foreground">
                            {submission['Task Type']}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm">{submission['Miner/ Slicer Name']}</div>
                          <div className="text-xs text-muted-foreground">
                            Leader: {submission['Leader Name'] || 'None'}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(submission.Timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge 
                          variant={
                            submission['Is this rejected (Slice / Miner)'] === 'Accepted' 
                              ? 'default' 
                              : submission['Is this rejected (Slice / Miner)'] === 'Rejected'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {submission['Is this rejected (Slice / Miner)'] || 'Pending'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No submissions found matching your filters
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Members ({users.length})</CardTitle>
              <CardDescription>
                All registered users and their roles
              </CardDescription>
            </CardHeader>
            <CardContent>
              {users.length > 0 ? (
                <div className="space-y-4">
                  {users.map((user, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium">{user.Email}</div>
                      </div>
                      <Badge variant={user.Role === 'admin' ? 'default' : 'secondary'}>
                        {user.Role}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No users found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AdminDashboard

