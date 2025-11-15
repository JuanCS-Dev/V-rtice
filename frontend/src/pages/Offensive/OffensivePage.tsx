import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui";
import { Shield, Wifi, AlertTriangle } from "lucide-react";
import { NetworkScanForm } from "@/features/offensive/components/NetworkScanForm";
import { VulnScanForm } from "@/features/offensive/components/VulnScanForm";

export default function OffensivePage() {
  const [activeTab, setActiveTab] = useState("network");

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          Offensive Security
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          Network scanning, vulnerability detection, and penetration testing
          tools
        </p>
      </div>

      {/* Tabs for different offensive tools */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="network">
            <Wifi className="mr-2 h-4 w-4" />
            Network Scan
          </TabsTrigger>
          <TabsTrigger value="vuln">
            <AlertTriangle className="mr-2 h-4 w-4" />
            Vulnerability Scan
          </TabsTrigger>
        </TabsList>

        <TabsContent value="network" className="mt-6">
          <NetworkScanForm />
        </TabsContent>

        <TabsContent value="vuln" className="mt-6">
          <VulnScanForm />
        </TabsContent>
      </Tabs>

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" />
            <CardTitle>Offensive Security Tools</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Use these tools responsibly and only on systems you have explicit
            permission to test. All activities are logged and monitored for
            compliance.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
