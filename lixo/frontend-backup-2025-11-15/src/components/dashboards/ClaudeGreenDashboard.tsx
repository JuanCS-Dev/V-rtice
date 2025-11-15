/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CLAUDE GREEN DASHBOARD - EXEMPLO COMPLETO
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard exemplo usando TODOS os componentes Claude.ai GREEN
 *
 * Blueprint para migrar outros dashboards:
 * - AdminDashboard
 * - OSINTDashboard
 * - CyberDashboard
 * - MaximusDashboard
 * - etc.
 *
 * VERDE (#10b981), NÃO LARANJA
 */

import React from 'react'
import {
  // Layout
  Navbar,
  Sidebar,
  Container,
  Grid,
  Stack,
  // Core
  Button,
  Input,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  // Widgets
  StatCard,
  MetricCard,
  DataTable,
  // Feedback
  Alert,
  AlertTitle,
  AlertDescription,
  Spinner,
} from '../ui/claude'
import {
  Home,
  BarChart3,
  Settings,
  Users,
  Activity,
  Shield,
  TrendingUp,
  AlertCircle,
  Search,
  Bell,
  User,
} from 'lucide-react'

/**
 * Claude Green Dashboard - EXEMPLO COMPLETO
 *
 * Demonstra:
 * - Navbar com verde accents
 * - Sidebar collapsible com verde active
 * - StatCards com trending verde
 * - DataTable com sort verde
 * - Responsive grid
 * - Alert verde success
 * - ZERO laranja/vermelho
 */
export function ClaudeGreenDashboard() {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

  // Navigation items
  const navItems = [
    { label: 'Dashboard', href: '#', active: true },
    { label: 'Analytics', href: '#' },
    { label: 'Reports', href: '#', badge: '3' },
    {
      label: 'More',
      children: [
        { label: 'Settings', href: '#' },
        { label: 'Help', href: '#' },
      ],
    },
  ]

  const sidebarItems = [
    { label: 'Home', icon: <Home className="w-5 h-5" />, href: '#', active: true },
    { label: 'Analytics', icon: <BarChart3 className="w-5 h-5" />, href: '#' },
    { label: 'Users', icon: <Users className="w-5 h-5" />, href: '#', badge: '12' },
    { label: 'Activity', icon: <Activity className="w-5 h-5" />, href: '#' },
    { label: 'Security', icon: <Shield className="w-5 h-5" />, href: '#', badge: '2', badgeVariant: 'warning' as const },
    { label: 'Settings', icon: <Settings className="w-5 h-5" />, href: '#' },
  ]

  // Sample data for table
  const tableData = [
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'Active', role: 'Admin' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'Active', role: 'User' },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'Inactive', role: 'User' },
    { id: 4, name: 'Alice Brown', email: 'alice@example.com', status: 'Active', role: 'Moderator' },
  ]

  const tableColumns = [
    { key: 'name', title: 'Name', sortable: true },
    { key: 'email', title: 'Email', sortable: true },
    {
      key: 'status',
      title: 'Status',
      render: (value: string) => (
        <Badge variant={value === 'Active' ? 'success' : 'secondary'}>
          {value}
        </Badge>
      ),
    },
    { key: 'role', title: 'Role' },
  ]

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Navbar */}
      <Navbar
        logo={
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6" style={{ color: 'var(--primary)' }} />
            <span className="text-xl font-bold font-[var(--font-display)]" style={{ color: 'var(--primary)' }}>
              VÉRTICE 💚
            </span>
          </div>
        }
        navItems={navItems}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon">
              <Search className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Bell className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <User className="w-5 h-5" />
            </Button>
            <Button size="sm">💚 New Item</Button>
          </div>
        }
        mobileMenuOpen={mobileMenuOpen}
        onMobileMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)}
      />

      {/* Main Layout */}
      <div className="flex">
        {/* Sidebar */}
        <Sidebar
          items={sidebarItems}
          collapsed={sidebarCollapsed}
          onCollapsedChange={setSidebarCollapsed}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Container size="2xl" className="py-8">
            <Stack gap="xl">
              {/* Header */}
              <div>
                <h1 className="text-4xl font-bold font-[var(--font-display)] mb-2">
                  Dashboard Overview 💚
                </h1>
                <p className="text-[var(--muted-foreground)] font-[var(--font-primary)]">
                  Claude.ai Green Design System - ZERO Laranja, 100% Verde
                </p>
              </div>

              {/* Alert Success - Verde! */}
              <Alert variant="success">
                <AlertTitle>Sistema Migrado com Sucesso! 💚</AlertTitle>
                <AlertDescription>
                  Todos os componentes agora usam VERDE (#10b981) ao invés de laranja.
                  Design system Claude.ai aplicado com perfeição.
                </AlertDescription>
              </Alert>

              {/* Stats Grid */}
              <Grid cols={4} gap="lg">
                <StatCard
                  title="Total Users"
                  value="2,543"
                  trend={{ value: 12.5, direction: 'up', label: 'vs last month' }}
                  icon={Users}
                />
                <StatCard
                  title="Active Sessions"
                  value="1,234"
                  trend={{ value: 8.2, direction: 'up' }}
                  icon={Activity}
                  variant="success"
                />
                <StatCard
                  title="Security Alerts"
                  value="23"
                  trend={{ value: -15.3, direction: 'down', label: 'improvement' }}
                  icon={AlertCircle}
                  variant="warning"
                />
                <StatCard
                  title="System Health"
                  value="98.9%"
                  trend={{ value: 0.5, direction: 'up' }}
                  icon={TrendingUp}
                />
              </Grid>

              {/* Metric Cards */}
              <Grid cols={3} gap="lg">
                <MetricCard
                  title="Response Time"
                  subtitle="Average"
                  value="124ms"
                  icon={Activity}
                  description="Excellent performance"
                />
                <MetricCard
                  title="Uptime"
                  subtitle="Last 30 days"
                  value="99.95%"
                  icon={Shield}
                  description="SLA compliant"
                />
                <MetricCard
                  title="Requests"
                  subtitle="Per second"
                  value="1.2K"
                  icon={BarChart3}
                  description="Peak: 2.5K"
                />
              </Grid>

              {/* Data Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Users</CardTitle>
                  <CardDescription>
                    User activity with verde sort indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DataTable
                    columns={tableColumns}
                    data={tableData}
                    onRowClick={(row) => console.log('Clicked:', row)}
                  />
                </CardContent>
              </Card>

              {/* Search Example */}
              <Card>
                <CardHeader>
                  <CardTitle>Search & Filters 💚</CardTitle>
                  <CardDescription>
                    Form components with verde focus rings
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Input placeholder="Search users..." />
                    </div>
                    <Button>Search</Button>
                    <Button variant="outline">Clear</Button>
                  </div>
                </CardContent>
              </Card>

              {/* Footer */}
              <div className="text-center py-8 border-t border-[var(--border)]">
                <p className="text-[var(--muted-foreground)] font-[var(--font-primary)]">
                  <strong style={{ color: 'var(--primary)' }}>VERDE (#10b981)</strong> em todos os accents |
                  ZERO laranja/vermelho | Claude.ai aesthetic | SOLI DEO GLORIA 💚
                </p>
              </div>
            </Stack>
          </Container>
        </main>
      </div>
    </div>
  )
}

export default ClaudeGreenDashboard
