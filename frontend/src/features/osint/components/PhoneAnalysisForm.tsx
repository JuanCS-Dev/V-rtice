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
  Phone,
  MapPin,
  User,
  Calendar,
  AlertCircle,
} from "lucide-react";
import {
  osintService,
  type PhoneAnalysisRequest,
  type PhoneAnalysisResponse,
} from "@/services/api/osintService";

const phoneSchema = z.object({
  phone: z
    .string()
    .min(1, "Phone number is required")
    .regex(/^[\d+\-() ]+$/, "Invalid phone number format"),
});

type PhoneFormData = z.infer<typeof phoneSchema>;

export function PhoneAnalysisForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PhoneAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PhoneFormData>({
    resolver: zodResolver(phoneSchema),
  });

  const onSubmit = async (data: PhoneFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: PhoneAnalysisRequest = {
        phone: data.phone,
      };

      const analysis = await osintService.analyzePhone(request);
      setResult(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze phone number");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Phone Number Analysis</CardTitle>
        <CardDescription>
          OSINT intelligence gathering from phone numbers
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Phone Input */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Phone Number
            </label>
            <Input
              {...register("phone")}
              placeholder="+55 11 98765-4321"
              className="font-mono"
            />
            {errors.phone && (
              <p className="mt-1 text-xs text-red-600">
                {errors.phone.message}
              </p>
            )}
            <p className="mt-1.5 text-xs text-[rgb(var(--text-tertiary))]">
              Include country code (e.g., +55 for Brazil)
            </p>
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
                <Phone className="mr-2 h-4 w-4" />
                Analyze Phone
              </>
            )}
          </Button>
        </form>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Analysis Results
              </h3>
              <Badge variant={result.is_valid ? "success" : "danger"}>
                {result.is_valid ? "Valid" : "Invalid"}
              </Badge>
            </div>

            {/* Phone Details */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                Phone Details
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Number
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.phone}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Country
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.country_name} ({result.country_code})
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Carrier
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.carrier || "Unknown"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Line Type
                  </span>
                  <Badge variant="default">{result.line_type}</Badge>
                </div>
              </div>
            </div>

            {/* Location Info */}
            {result.location && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  <MapPin className="h-4 w-4 text-primary-600" />
                  Location Information
                </h4>
                <div className="space-y-2">
                  {result.location.city && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        City
                      </span>
                      <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.location.city}
                      </span>
                    </div>
                  )}
                  {result.location.state && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        State
                      </span>
                      <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.location.state}
                      </span>
                    </div>
                  )}
                  {result.location.timezone && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Timezone
                      </span>
                      <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.location.timezone}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Social Profiles */}
            {result.social_profiles && result.social_profiles.length > 0 && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  <User className="h-4 w-4 text-primary-600" />
                  Social Media Profiles ({result.social_profiles.length})
                </h4>
                <div className="space-y-2">
                  {result.social_profiles.map((profile, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-primary-200 bg-primary-50 p-2 dark:border-primary-800 dark:bg-primary-950"
                    >
                      <span className="text-sm font-medium text-primary-900 dark:text-primary-100">
                        {profile.platform}
                      </span>
                      <a
                        href={profile.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary-600 hover:underline dark:text-primary-400"
                      >
                        View Profile
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reputation */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                Reputation Analysis
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                      Reputation Score
                    </span>
                    <span
                      className={`text-sm font-bold ${
                        result.reputation_score >= 70
                          ? "text-primary-600"
                          : result.reputation_score >= 40
                            ? "text-amber-600"
                            : "text-red-600"
                      }`}
                    >
                      {result.reputation_score}/100
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-[rgb(var(--border))]">
                    <div
                      className={`h-full transition-all ${
                        result.reputation_score >= 70
                          ? "bg-primary-500"
                          : result.reputation_score >= 40
                            ? "bg-amber-500"
                            : "bg-red-500"
                      }`}
                      style={{ width: `${result.reputation_score}%` }}
                    />
                  </div>
                </div>

                {result.risk_flags && result.risk_flags.length > 0 && (
                  <div>
                    <span className="mb-2 block text-xs font-medium text-[rgb(var(--text-secondary))]">
                      Risk Flags
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {result.risk_flags.map((flag, idx) => (
                        <Badge key={idx} variant="warning">
                          {flag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Metadata */}
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
