import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Badge,
} from "@/components/ui";
import { Loader2, CheckCircle2, XCircle, Clock, Zap } from "lucide-react";
import {
  maximusService,
  type AuroraInvestigation,
} from "@/services/api/maximusService";

const investigationSchema = z.object({
  target: z.string().min(1, "Target is required"),
  services: z.array(z.string()).optional(),
});

type InvestigationFormData = z.infer<typeof investigationSchema>;

export function InvestigationPanel() {
  const [isLoading, setIsLoading] = useState(false);
  const [investigation, setInvestigation] =
    useState<AuroraInvestigation | null>(null);
  const [availableServices, setAvailableServices] = useState<string[]>([]);
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<InvestigationFormData>({
    resolver: zodResolver(investigationSchema),
  });

  useEffect(() => {
    // Fetch available services on mount
    const fetchServices = async () => {
      try {
        const services = await maximusService.getAvailableServices();
        setAvailableServices(services);
      } catch (err) {
        console.error("Failed to fetch services:", err);
      }
    };
    fetchServices();

    // Cleanup polling on unmount
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, []);

  const pollInvestigation = async (investigationId: string) => {
    try {
      const updated = await maximusService.getInvestigation(investigationId);
      setInvestigation(updated);

      // Stop polling if completed or failed
      if (updated.status === "completed" || updated.status === "failed") {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        setIsLoading(false);
      }
    } catch (err) {
      console.error("Failed to poll investigation:", err);
    }
  };

  const onSubmit = async (data: InvestigationFormData) => {
    setIsLoading(true);
    setError(null);
    setInvestigation(null);

    try {
      const inv = await maximusService.investigate(
        data.target,
        selectedServices.length > 0 ? selectedServices : undefined,
      );
      setInvestigation(inv);

      // Start polling if not completed
      if (inv.status !== "completed" && inv.status !== "failed") {
        const interval = setInterval(
          () => pollInvestigation(inv.investigation_id),
          2000,
        );
        setPollingInterval(interval);
      } else {
        setIsLoading(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start investigation");
      setIsLoading(false);
    }
  };

  const toggleService = (service: string) => {
    setSelectedServices((prev) =>
      prev.includes(service)
        ? prev.filter((s) => s !== service)
        : [...prev, service],
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-primary-600" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-amber-600" />;
      case "queued":
        return <Clock className="h-4 w-4 text-gray-600" />;
      default:
        return null;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "danger";
      case "running":
        return "warning";
      case "queued":
        return "default";
      default:
        return "default";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aurora Investigation Orchestrator</CardTitle>
        <CardDescription>
          Automated multi-service OSINT investigation powered by AI
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Target Input */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Investigation Target
            </label>
            <Input
              {...register("target")}
              placeholder="email@example.com, +1234567890, domain.com, 192.168.1.1"
            />
            {errors.target && (
              <p className="mt-1 text-xs text-red-600">
                {errors.target.message}
              </p>
            )}
            <p className="mt-1.5 text-xs text-[rgb(var(--text-tertiary))]">
              Aurora will automatically detect the target type and use relevant
              services
            </p>
          </div>

          {/* Service Selection */}
          {availableServices.length > 0 && (
            <div>
              <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
                Services (Optional - leave empty for auto-detection)
              </label>
              <div className="flex flex-wrap gap-2">
                {availableServices.map((service) => (
                  <button
                    key={service}
                    type="button"
                    onClick={() => toggleService(service)}
                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                      selectedServices.includes(service)
                        ? "bg-primary-500 text-white"
                        : "border border-[rgb(var(--border))] text-[rgb(var(--text-primary))] hover:border-primary-500"
                    }`}
                  >
                    {service}
                  </button>
                ))}
              </div>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Investigating...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                Start Investigation
              </>
            )}
          </Button>
        </form>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Investigation Results */}
        {investigation && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Investigation Status
              </h3>
              <Badge variant={getStatusVariant(investigation.status)}>
                {investigation.status}
              </Badge>
            </div>

            {/* Investigation Info */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Investigation ID
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {investigation.investigation_id}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Target
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {investigation.target}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Started At
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {new Date(investigation.started_at).toLocaleString()}
                  </span>
                </div>
                {investigation.completed_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[rgb(var(--text-secondary))]">
                      Completed At
                    </span>
                    <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                      {new Date(investigation.completed_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Services Used */}
            {investigation.services_used.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  Services Used ({investigation.services_used.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {investigation.services_used.map((service, idx) => (
                    <Badge key={idx} variant="default">
                      {service}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Findings */}
            {investigation.findings.length > 0 && (
              <div>
                <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  Findings ({investigation.findings.length})
                </h4>
                <div className="space-y-2">
                  {investigation.findings
                    .sort((a, b) => b.relevance - a.relevance)
                    .map((finding, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-[rgb(var(--border))] p-3"
                      >
                        <div className="mb-2 flex items-center justify-between">
                          <Badge variant="default">{finding.service}</Badge>
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-[rgb(var(--text-secondary))]">
                              Relevance
                            </span>
                            <span className="text-xs font-semibold text-primary-600">
                              {(finding.relevance * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <pre className="overflow-x-auto rounded-md bg-[rgb(var(--background))] p-2 font-mono text-xs text-[rgb(var(--text-primary))]">
                          {JSON.stringify(finding.data, null, 2)}
                        </pre>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* AI Summary */}
            {investigation.summary && (
              <div className="rounded-lg border border-primary-200 bg-primary-50 p-4 dark:border-primary-800 dark:bg-primary-950">
                <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-primary-900 dark:text-primary-100">
                  <Zap className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                  AI-Generated Summary
                </h4>
                <p className="text-sm text-primary-700 dark:text-primary-300">
                  {investigation.summary}
                </p>
              </div>
            )}

            {/* Progress Indicator */}
            {investigation.status === "running" && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-amber-600 dark:text-amber-400" />
                  <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                    Investigation in progress... Polling for updates every 2
                    seconds
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
