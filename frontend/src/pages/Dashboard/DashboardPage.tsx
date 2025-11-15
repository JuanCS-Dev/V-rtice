import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";
import { LineChart, BarChart, PieChart } from "@/components/charts";
import { Activity } from "lucide-react";

export default function DashboardPage() {
  const weekData = [
    { day: "Mon", value: 45 },
    { day: "Tue", value: 52 },
    { day: "Wed", value: 38 },
    { day: "Thu", value: 67 },
    { day: "Fri", value: 71 },
    { day: "Sat", value: 28 },
    { day: "Sun", value: 34 },
  ];

  const threatSeverity = [
    { severity: "Critical", count: 2 },
    { severity: "High", count: 5 },
    { severity: "Medium", count: 12 },
    { severity: "Low", count: 23 },
    { severity: "Info", count: 45 },
  ];

  const serviceData = [
    { service: "OSINT", requests: 847 },
    { service: "Immunis", requests: 523 },
    { service: "Offensive", requests: 234 },
    { service: "Defensive", requests: 678 },
    { service: "MAXIMUS", requests: 412 },
  ];

  const threatStatus = [
    { name: "Active", value: 12 },
    { name: "Resolved", value: 245 },
  ];

  const scanStatus = [
    { name: "Running", value: 8 },
    { name: "Completed", value: 156 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3.5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[rgb(var(--text-primary))] leading-none">
            Dashboard
          </h1>
          <p className="text-[11px] text-[rgb(var(--text-tertiary))] mt-2 font-medium tracking-wide leading-none">
            Vértice v3.3.1 <span className="text-[rgb(var(--border))]">•</span>{" "}
            Cybersecurity Command Center
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-2.5 py-1.5 shadow-sm self-start transition-all duration-200 hover:shadow-md hover:border-[rgb(var(--border))]/60">
          <Activity
            className="h-3.5 w-3.5 text-primary-500"
            strokeWidth={2.5}
          />
          <span className="text-[11px] font-semibold text-[rgb(var(--text-secondary))] leading-none">
            All systems operational
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Threats
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5">
              <PieChart data={threatStatus} height={120} />
              <div className="text-center sm:text-left">
                <div className="text-3xl font-bold tabular-nums leading-none">
                  257
                </div>
                <div className="text-[10px] text-[rgb(var(--text-tertiary))] uppercase tracking-wider font-medium mt-1.5 leading-none">
                  Total
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs leading-none">
                    <div className="w-2 h-2 rounded-full bg-[#10b981] ring-1 ring-[#10b981]/20" />
                    <span className="text-[rgb(var(--text-secondary))] font-medium">
                      Active:{" "}
                      <span className="text-[rgb(var(--text-primary))] tabular-nums font-semibold">
                        12
                      </span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs leading-none">
                    <div className="w-2 h-2 rounded-full bg-[#6b7280] ring-1 ring-[#6b7280]/20" />
                    <span className="text-[rgb(var(--text-secondary))] font-medium">
                      Resolved:{" "}
                      <span className="text-[rgb(var(--text-primary))] tabular-nums font-semibold">
                        245
                      </span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Scans
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5">
              <PieChart data={scanStatus} height={120} />
              <div className="text-center sm:text-left">
                <div className="text-3xl font-bold tabular-nums leading-none">
                  164
                </div>
                <div className="text-[10px] text-[rgb(var(--text-tertiary))] uppercase tracking-wider font-medium mt-1.5 leading-none">
                  Total
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs leading-none">
                    <div className="w-2 h-2 rounded-full bg-[#10b981] ring-1 ring-[#10b981]/20" />
                    <span className="text-[rgb(var(--text-secondary))] font-medium">
                      Running:{" "}
                      <span className="text-[rgb(var(--text-primary))] tabular-nums font-semibold">
                        8
                      </span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs leading-none">
                    <div className="w-2 h-2 rounded-full bg-[#6b7280] ring-1 ring-[#6b7280]/20" />
                    <span className="text-[rgb(var(--text-secondary))] font-medium">
                      Done:{" "}
                      <span className="text-[rgb(var(--text-primary))] tabular-nums font-semibold">
                        156
                      </span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Threat Severity
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <BarChart
              data={threatSeverity}
              bars={[{ dataKey: "count", fill: "#10b981" }]}
              xAxisKey="severity"
              height={160}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Weekly Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <BarChart
              data={weekData}
              bars={[{ dataKey: "value", fill: "#10b981" }]}
              xAxisKey="day"
              height={160}
            />
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Service Usage (24h)
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <BarChart
              data={serviceData}
              bars={[{ dataKey: "requests", fill: "#10b981" }]}
              xAxisKey="service"
              height={160}
            />
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              Threat Timeline (7d)
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <LineChart
              data={weekData}
              lines={[{ dataKey: "value", stroke: "#10b981" }]}
              xAxisKey="day"
              height={200}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-[rgb(var(--text-secondary))] leading-none">
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent className="px-6 pb-5">
            <div className="space-y-2.5">
              {[
                { name: "API Gateway", latency: "12ms" },
                { name: "MAXIMUS", latency: "45ms" },
                { name: "Immunis", latency: "23ms" },
                { name: "OSINT", latency: "156ms" },
              ].map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between leading-none"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-2 w-2 rounded-full bg-primary-500 ring-1 ring-primary-500/20" />
                    <span className="font-semibold text-[rgb(var(--text-primary))] text-xs">
                      {service.name}
                    </span>
                  </div>
                  <span className="text-[rgb(var(--text-tertiary))] font-mono text-[11px] tabular-nums font-medium">
                    {service.latency}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
