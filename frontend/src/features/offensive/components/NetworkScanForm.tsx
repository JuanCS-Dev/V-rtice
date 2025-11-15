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
import { Loader2, Play } from "lucide-react";
import {
  offensiveService,
  type NmapScanRequest,
  type NmapScanResponse,
} from "@/services/api/offensiveService";

const scanSchema = z.object({
  target: z
    .string()
    .min(1, "Target is required")
    .refine(
      (val) => {
        // Validate IP or hostname
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/;
        const hostnameRegex =
          /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/;
        return ipRegex.test(val) || hostnameRegex.test(val);
      },
      { message: "Invalid IP address or hostname" },
    ),
  scan_type: z.enum(["quick", "intense", "ping", "custom"]).default("quick"),
  ports: z.string().optional(),
});

type ScanFormData = z.infer<typeof scanSchema>;

export function NetworkScanForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState<NmapScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ScanFormData>({
    resolver: zodResolver(scanSchema),
    defaultValues: {
      scan_type: "quick",
    },
  });

  const scanType = watch("scan_type");

  const onSubmit = async (data: ScanFormData) => {
    setIsLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const request: NmapScanRequest = {
        target: data.target,
        scan_type: data.scan_type,
        ...(data.ports && { ports: data.ports }),
      };

      const result = await offensiveService.startNmapScan(request);
      setScanResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start scan");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Network Scanner (Nmap)</CardTitle>
        <CardDescription>
          Scan network hosts and discover open ports
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
              placeholder="192.168.1.0/24 or example.com"
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
              {["quick", "intense", "ping", "custom"].map((type) => (
                <label
                  key={type}
                  className={`
                    flex items-center justify-center rounded-lg border-2 px-4 py-3 cursor-pointer transition-all
                    ${
                      scanType === type
                        ? "border-primary-500 bg-primary-500/10 text-primary-600"
                        : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
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

          {/* Ports (if custom) */}
          {scanType === "custom" && (
            <div>
              <label className="block text-sm font-medium text-[rgb(var(--text-primary))] mb-1.5">
                Ports (optional)
              </label>
              <Input {...register("ports")} placeholder="22,80,443 or 1-1024" />
              <p className="mt-1 text-xs text-[rgb(var(--text-secondary))]">
                Leave empty to scan common ports
              </p>
            </div>
          )}

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
                <Play className="mr-2 h-4 w-4" />
                Start Scan
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
                  scanResult.status === "completed"
                    ? "success"
                    : scanResult.status === "running"
                      ? "warning"
                      : "default"
                }
              >
                {scanResult.status}
              </Badge>
            </div>

            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-[rgb(var(--text-secondary))]">
                    Scan ID:
                  </span>
                  <p className="font-mono text-xs text-[rgb(var(--text-primary))]">
                    {scanResult.scan_id}
                  </p>
                </div>
                <div>
                  <span className="text-[rgb(var(--text-secondary))]">
                    Target:
                  </span>
                  <p className="font-semibold text-[rgb(var(--text-primary))]">
                    {scanResult.target}
                  </p>
                </div>
                <div>
                  <span className="text-[rgb(var(--text-secondary))]">
                    Started:
                  </span>
                  <p className="text-[rgb(var(--text-primary))]">
                    {new Date(scanResult.start_time).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-[rgb(var(--text-secondary))]">
                    Hosts Found:
                  </span>
                  <p className="font-semibold text-primary-600">
                    {scanResult.results?.hosts?.length || 0}
                  </p>
                </div>
              </div>

              {/* Hosts */}
              {scanResult.results?.hosts &&
                scanResult.results.hosts.length > 0 && (
                  <div className="mt-4 space-y-3">
                    {scanResult.results.hosts.map((host, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-[rgb(var(--border))] p-3"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <p className="font-semibold text-[rgb(var(--text-primary))]">
                              {host.ip}
                            </p>
                            {host.hostname && (
                              <p className="text-xs text-[rgb(var(--text-secondary))]">
                                {host.hostname}
                              </p>
                            )}
                          </div>
                          <Badge variant="success">{host.state}</Badge>
                        </div>
                        <div className="text-xs">
                          <span className="text-[rgb(var(--text-secondary))]">
                            Open ports:{" "}
                            {
                              host.ports.filter((p) => p.state === "open")
                                .length
                            }
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
