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
import {
  Loader2,
  Globe,
  MapPin,
  Shield,
  AlertTriangle,
  Server,
  Calendar,
} from "lucide-react";
import {
  osintService,
  type IPAnalysisRequest,
  type IPAnalysisResponse,
} from "@/services/api/osintService";

const ipSchema = z.object({
  ip: z
    .string()
    .min(1, "IP address is required")
    .regex(
      /^(\d{1,3}\.){3}\d{1,3}$/,
      "Invalid IPv4 address format (e.g., 192.168.1.1)",
    ),
});

type IPFormData = z.infer<typeof ipSchema>;

export function IPAnalysisForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<IPAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<IPFormData>({
    resolver: zodResolver(ipSchema),
  });

  const onSubmit = async (data: IPFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: IPAnalysisRequest = {
        ip: data.ip,
      };

      const analysis = await osintService.analyzeIP(request);
      setResult(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze IP address");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>IP Address Analysis</CardTitle>
        <CardDescription>
          Geolocation, threat intelligence, and network information
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* IP Input */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              IP Address
            </label>
            <Input
              {...register("ip")}
              placeholder="192.168.1.1"
              className="font-mono"
            />
            {errors.ip && (
              <p className="mt-1 text-xs text-red-600">{errors.ip.message}</p>
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
                Analyzing...
              </>
            ) : (
              <>
                <Globe className="mr-2 h-4 w-4" />
                Analyze IP
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
        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Analysis Results
              </h3>
              <Badge variant={result.is_malicious ? "danger" : "success"}>
                {result.is_malicious ? "Malicious" : "Clean"}
              </Badge>
            </div>

            {/* IP Info */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                <Server className="h-4 w-4 text-primary-600" />
                IP Information
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    IP Address
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.ip}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Hostname
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.hostname || "N/A"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    ASN
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.asn || "N/A"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    ISP
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.isp || "N/A"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Organization
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.organization || "N/A"}
                  </span>
                </div>
              </div>
            </div>

            {/* Geolocation */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                <MapPin className="h-4 w-4 text-primary-600" />
                Geolocation
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Country
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.country} ({result.country_code})
                  </span>
                </div>
                {result.region && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[rgb(var(--text-secondary))]">
                      Region
                    </span>
                    <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                      {result.region}
                    </span>
                  </div>
                )}
                {result.city && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[rgb(var(--text-secondary))]">
                      City
                    </span>
                    <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                      {result.city}
                    </span>
                  </div>
                )}
                {result.latitude && result.longitude && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Coordinates
                      </span>
                      <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.latitude}, {result.longitude}
                      </span>
                    </div>
                    <a
                      href={`https://www.google.com/maps?q=${result.latitude},${result.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400"
                    >
                      View on Google Maps
                    </a>
                  </>
                )}
              </div>
            </div>

            {/* Threat Intelligence */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                <Shield className="h-4 w-4 text-primary-600" />
                Threat Intelligence
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                      Threat Score
                    </span>
                    <span
                      className={`text-sm font-bold ${
                        result.threat_score > 70
                          ? "text-red-600"
                          : result.threat_score > 40
                            ? "text-amber-600"
                            : "text-primary-600"
                      }`}
                    >
                      {result.threat_score}/100
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-[rgb(var(--border))]">
                    <div
                      className={`h-full transition-all ${
                        result.threat_score > 70
                          ? "bg-red-500"
                          : result.threat_score > 40
                            ? "bg-amber-500"
                            : "bg-primary-500"
                      }`}
                      style={{ width: `${result.threat_score}%` }}
                    />
                  </div>
                </div>

                {result.blacklists && result.blacklists.length > 0 && (
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                        Blacklists ({result.blacklists.length})
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {result.blacklists.map((bl, idx) => (
                        <Badge key={idx} variant="danger">
                          {bl}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {result.threat_categories &&
                  result.threat_categories.length > 0 && (
                    <div>
                      <span className="mb-2 block text-xs font-medium text-[rgb(var(--text-secondary))]">
                        Threat Categories
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {result.threat_categories.map((cat, idx) => (
                          <Badge key={idx} variant="warning">
                            {cat}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>

            {/* Additional Info */}
            {result.additional_info &&
              Object.keys(result.additional_info).length > 0 && (
                <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                  <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                    Additional Information
                  </h4>
                  <div className="space-y-1">
                    {Object.entries(result.additional_info).map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between"
                        >
                          <span className="text-xs text-[rgb(var(--text-secondary))]">
                            {key}
                          </span>
                          <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                            {String(value)}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}

            {/* Timestamp */}
            <div className="flex items-center gap-2 text-xs text-[rgb(var(--text-tertiary))]">
              <Calendar className="h-3.5 w-3.5" />
              <span>
                Analyzed at {new Date(result.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
