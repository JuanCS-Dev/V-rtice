import { useState } from "react";
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
import { Loader2, Shield, AlertTriangle } from "lucide-react";
import {
  offensiveService,
  type VulnScanRequest,
  type VulnScanResponse,
} from "@/services/api/offensiveService";

const vulnScanSchema = z.object({
  target: z
    .string()
    .min(1, "Target is required")
    .refine(
      (val) => {
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
        const urlRegex = /^https?:\/\/.+/;
        return ipRegex.test(val) || urlRegex.test(val);
      },
      { message: "Invalid IP address or URL" },
    ),
  scan_type: z.enum(["basic", "full", "web", "network"]).default("basic"),
  depth: z.enum(["shallow", "medium", "deep"]).default("medium"),
});

type VulnScanFormData = z.infer<typeof vulnScanSchema>;

export function VulnScanForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState<VulnScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<VulnScanFormData>({
    resolver: zodResolver(vulnScanSchema),
    defaultValues: {
      scan_type: "basic",
      depth: "medium",
    },
  });

  const scanType = watch("scan_type");
  const depth = watch("depth");

  const onSubmit = async (data: VulnScanFormData) => {
    setIsLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const request: VulnScanRequest = {
        target: data.target,
        scan_type: data.scan_type,
        depth: data.depth,
      };

      const result = await offensiveService.startVulnScan(request);
      setScanResult(result);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to start vulnerability scan",
      );
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vulnerability Scanner</CardTitle>
        <CardDescription>
          Automated vulnerability detection and assessment
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Target */}
          <div>
            <label className="block text-sm font-medium text-[rgb(var(--text-primary))] mb-1.5">
              Target
            </label>
            <Input
              {...register("target")}
              placeholder="192.168.1.100 or https://example.com"
              className={errors.target ? "border-red-500" : ""}
            />
            {errors.target && (
              <p className="mt-1 text-xs text-red-600">
                {errors.target.message}
              </p>
            )}
          </div>

          {/* Scan Type */}
          <div>
            <label className="block text-sm font-medium text-[rgb(var(--text-primary))] mb-1.5">
              Scan Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {["basic", "full", "web", "network"].map((type) => (
                <label
                  key={type}
                  className={`
                    flex items-center justify-center rounded-lg border-2 px-4 py-2.5 cursor-pointer transition-all
                    ${
                      scanType === type
                        ? "border-primary-500 bg-primary-500/10 text-primary-600"
                        : "border-gray-200 hover:border-gray-300 dark:border-gray-700"
                    }
                  `}
                >
                  <input
                    type="radio"
                    {...register("scan_type")}
                    value={type}
                    className="sr-only"
                  />
                  <span className="text-sm font-medium capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Depth */}
          <div>
            <label className="block text-sm font-medium text-[rgb(var(--text-primary))] mb-1.5">
              Scan Depth
            </label>
            <div className="grid grid-cols-3 gap-2">
              {["shallow", "medium", "deep"].map((d) => (
                <label
                  key={d}
                  className={`
                    flex items-center justify-center rounded-lg border-2 px-4 py-2.5 cursor-pointer transition-all
                    ${
                      depth === d
                        ? "border-primary-500 bg-primary-500/10 text-primary-600"
                        : "border-gray-200 hover:border-gray-300 dark:border-gray-700"
                    }
                  `}
                >
                  <input
                    type="radio"
                    {...register("depth")}
                    value={d}
                    className="sr-only"
                  />
                  <span className="text-sm font-medium capitalize">{d}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Shield className="mr-2 h-4 w-4" />
                Start Vulnerability Scan
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

        {/* Results */}
        {scanResult && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Scan Results
              </h3>
              <Badge
                variant={
                  scanResult.status === "completed" ? "success" : "warning"
                }
              >
                {scanResult.status}
              </Badge>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-5 gap-3">
              <div className="rounded-lg border border-[rgb(var(--border))] p-3 text-center">
                <p className="text-2xl font-bold text-[rgb(var(--text-primary))]">
                  {scanResult.summary.total}
                </p>
                <p className="text-xs text-[rgb(var(--text-secondary))]">
                  Total
                </p>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center dark:border-red-800 dark:bg-red-950">
                <p className="text-2xl font-bold text-red-600">
                  {scanResult.summary.critical}
                </p>
                <p className="text-xs text-red-600">Critical</p>
              </div>
              <div className="rounded-lg border border-orange-200 bg-orange-50 p-3 text-center dark:border-orange-800 dark:bg-orange-950">
                <p className="text-2xl font-bold text-orange-600">
                  {scanResult.summary.high}
                </p>
                <p className="text-xs text-orange-600">High</p>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-center dark:border-amber-800 dark:bg-amber-950">
                <p className="text-2xl font-bold text-amber-600">
                  {scanResult.summary.medium}
                </p>
                <p className="text-xs text-amber-600">Medium</p>
              </div>
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-center dark:border-blue-800 dark:bg-blue-950">
                <p className="text-2xl font-bold text-blue-600">
                  {scanResult.summary.low}
                </p>
                <p className="text-xs text-blue-600">Low</p>
              </div>
            </div>

            {/* Vulnerabilities */}
            {scanResult.vulnerabilities.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-[rgb(var(--text-primary))]">
                  Vulnerabilities Found
                </h4>
                {scanResult.vulnerabilities.map((vuln, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-[rgb(var(--border))] p-4 space-y-2"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                          <h5 className="font-semibold text-[rgb(var(--text-primary))]">
                            {vuln.title}
                          </h5>
                        </div>
                        <p className="text-xs text-[rgb(var(--text-secondary))]">
                          {vuln.description}
                        </p>
                      </div>
                      <div className="ml-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getSeverityColor(vuln.severity)}`}
                        >
                          {vuln.severity.toUpperCase()}
                        </span>
                        {vuln.cvss_score && (
                          <p className="mt-1 text-xs text-[rgb(var(--text-secondary))]">
                            CVSS: {vuln.cvss_score}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-xs">
                      <span className="text-[rgb(var(--text-secondary))]">
                        Affected:{" "}
                      </span>
                      <span className="font-mono text-[rgb(var(--text-primary))]">
                        {vuln.affected_component}
                      </span>
                    </div>
                    {vuln.remediation && (
                      <div className="rounded bg-primary-50 p-2 dark:bg-primary-950">
                        <p className="text-xs text-primary-700 dark:text-primary-300">
                          <strong>Remediation:</strong> {vuln.remediation}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
