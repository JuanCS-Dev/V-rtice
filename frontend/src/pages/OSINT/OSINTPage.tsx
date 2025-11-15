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
import {
  Mail,
  Phone,
  Search,
  Image as ImageIcon,
  Globe,
  Eye,
} from "lucide-react";
import { EmailAnalysisForm } from "@/features/osint/components/EmailAnalysisForm";
import { PhoneAnalysisForm } from "@/features/osint/components/PhoneAnalysisForm";
import { GoogleSearchForm } from "@/features/osint/components/GoogleSearchForm";
import { ImageAnalysisForm } from "@/features/osint/components/ImageAnalysisForm";
import { IPAnalysisForm } from "@/features/osint/components/IPAnalysisForm";

export default function OSINTPage() {
  const [activeTab, setActiveTab] = useState("email");

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          OSINT Intelligence
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          Open-source intelligence gathering across multiple data sources
        </p>
      </div>

      {/* OSINT Tools Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="email">
            <Mail className="mr-2 h-4 w-4" />
            Email
          </TabsTrigger>
          <TabsTrigger value="phone">
            <Phone className="mr-2 h-4 w-4" />
            Phone
          </TabsTrigger>
          <TabsTrigger value="google">
            <Search className="mr-2 h-4 w-4" />
            Google
          </TabsTrigger>
          <TabsTrigger value="image">
            <ImageIcon className="mr-2 h-4 w-4" />
            Image
          </TabsTrigger>
          <TabsTrigger value="ip">
            <Globe className="mr-2 h-4 w-4" />
            IP Address
          </TabsTrigger>
        </TabsList>

        <TabsContent value="email" className="mt-6">
          <EmailAnalysisForm />
        </TabsContent>

        <TabsContent value="phone" className="mt-6">
          <PhoneAnalysisForm />
        </TabsContent>

        <TabsContent value="google" className="mt-6">
          <GoogleSearchForm />
        </TabsContent>

        <TabsContent value="image" className="mt-6">
          <ImageAnalysisForm />
        </TabsContent>

        <TabsContent value="ip" className="mt-6">
          <IPAnalysisForm />
        </TabsContent>
      </Tabs>

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-primary-600" />
            <CardTitle>OSINT Intelligence Gathering</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Collect and analyze publicly available information from various
            sources. All data is gathered from legitimate public sources and
            complies with applicable laws.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
