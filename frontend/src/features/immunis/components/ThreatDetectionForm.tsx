import { useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
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
import {
  Loader2,
  Shield,
  Plus,
  Trash2,
  AlertTriangle,
  Activity,
} from "lucide-react";
import {
  immunisService,
  type ThreatDetectRequest,
  type Threat,
} from "@/services/api/immunisService";

const threatSchema = z.object({
  source: z.string().min(1, "Source is required"),
  indicators: z
    .array(z.string().min(1, "Indicator cannot be empty"))
    .min(1, "At least one indicator is required"),
  severity: z.enum(["low", "medium", "high", "critical"]).optional(),
});

type ThreatFormData = z.infer<typeof threatSchema>;

export function ThreatDetectionForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<Threat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<ThreatFormData>({
    resolver: zodResolver(threatSchema),
    defaultValues: {
      source: "",
      indicators: [""],
      severity: "medium",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "indicators",
  });

  const onSubmit = async (data: ThreatFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: ThreatDetectRequest = {
        data: {
          source: data.source,
          indicators: data.indicators.filter((i) => i.trim() !== ""),
          severity: data.severity,
        },
      };

      const detection = await immunisService.detectThreat(request);
      setResult(detection);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to detect threat");
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-600 text-white";
      case "high":
        return "bg-orange-600 text-white";
      case "medium":
        return "bg-amber-600 text-white";
      case "low":
        return "bg-blue-600 text-white";
      default:
        return "bg-gray-600 text-white";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "danger";
      case "contained":
        return "warning";
      case "eliminated":
        return "success";
      default:
        return "default";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Threat Detection</CardTitle>
        <CardDescription>
          Immunis AI-powered threat detection and classification
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Source */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Threat Source
            </label>
            <Input
              {...register("source")}
              placeholder="e.g., IDS, Firewall, Network Monitor"
            />
            {errors.source && (
              <p className="mt-1 text-xs text-red-600">
                {errors.source.message}
              </p>
            )}
          </div>

          {/* Severity */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Severity Level
            </label>
            <select
              {...register("severity")}
              className="w-full rounded-lg border border-[rgb(var(--border))] px-3 py-2 text-sm"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Indicators */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-[rgb(var(--text-primary))]">
                Threat Indicators ({fields.length})
              </label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => append("")}
                className="h-8"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Indicator
              </Button>
            </div>

            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <Input
                  {...register(`indicators.${index}`)}
                  placeholder="e.g., 192.168.1.100, malware.exe, suspicious.com"
                  className="flex-1"
                />
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}

            {errors.indicators && (
              <p className="text-xs text-red-600">
                {errors.indicators.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Detecting...
              </>
            ) : (
              <>
                <Shield className="mr-2 h-4 w-4" />
                Detect Threat
              </>
            )}
          </Button>
        </form>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Threat Detection Results
              </h3>
              <div className="flex items-center gap-2">
                <Badge variant={getStatusColor(result.status)}>
                  {result.status}
                </Badge>
                <span
                  className={`rounded-md px-2 py-1 text-xs font-semibold ${getSeverityColor(result.severity)}`}
                >
                  {result.severity.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Threat Overview */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                Threat Overview
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Threat ID
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.threat_id}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Type
                  </span>
                  <Badge variant="default">{result.type}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Source
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.source}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Detected At
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {new Date(result.detected_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Confidence Score */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <div className="mb-1 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary-600" />
                  <span className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                    Detection Confidence
                  </span>
                </div>
                <span className="text-sm font-bold text-primary-600">
                  {(result.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-[rgb(var(--border))]">
                <div
                  className="h-full bg-primary-500 transition-all"
                  style={{ width: `${result.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Description */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                Description
              </h4>
              <p className="text-sm text-[rgb(var(--text-secondary))]">
                {result.description}
              </p>
            </div>

            {/* Indicators */}
            {result.indicators.length > 0 && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  Threat Indicators ({result.indicators.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {result.indicators.map((indicator, idx) => (
                    <Badge key={idx} variant="warning">
                      {indicator}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="rounded-lg border border-primary-200 bg-primary-50 p-4 dark:border-primary-800 dark:bg-primary-950">
              <div className="flex items-start gap-2">
                <Shield className="mt-0.5 h-4 w-4 text-primary-600 dark:text-primary-400" />
                <div>
                  <p className="text-sm font-semibold text-primary-900 dark:text-primary-100">
                    Immunis Response Active
                  </p>
                  <p className="mt-1 text-xs text-primary-700 dark:text-primary-300">
                    Immune agents have been deployed to contain and eliminate
                    this threat. Monitor the Immunis dashboard for real-time
                    updates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
