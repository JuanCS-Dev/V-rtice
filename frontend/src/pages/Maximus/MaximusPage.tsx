import { useState } from "react";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui";
import { Bot, Zap } from "lucide-react";
import { AIChatInterface } from "@/features/maximus/components/AIChatInterface";
import { InvestigationPanel } from "@/features/maximus/components/InvestigationPanel";

export default function MaximusPage() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          MAXIMUS AI
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          AI-powered decision making, investigation orchestration, and security
          analysis
        </p>
      </div>

      {/* Maximus Tools Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="chat">
            <Bot className="mr-2 h-4 w-4" />
            AI Assistant
          </TabsTrigger>
          <TabsTrigger value="aurora">
            <Zap className="mr-2 h-4 w-4" />
            Aurora Orchestrator
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="mt-6">
          <AIChatInterface />
        </TabsContent>

        <TabsContent value="aurora" className="mt-6">
          <InvestigationPanel />
        </TabsContent>
      </Tabs>

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary-600" />
            <CardTitle>MAXIMUS AI System</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Advanced AI assistant for security analysis and decision support.
            Aurora Orchestrator automatically coordinates multiple OSINT
            services for comprehensive investigations with AI-powered insights.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
