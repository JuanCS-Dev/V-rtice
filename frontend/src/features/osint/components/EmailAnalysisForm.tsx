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
  Mail,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import {
  osintService,
  type EmailAnalysisRequest,
  type EmailAnalysisResponse,
} from "@/services/api/osintService";

const emailSchema = z.object({
  email: z.string().email("Invalid email address"),
});

type EmailFormData = z.infer<typeof emailSchema>;

export function EmailAnalysisForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<EmailAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmailFormData>({
    resolver: zodResolver(emailSchema),
  });

  const onSubmit = async (data: EmailFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: EmailAnalysisRequest = { email: data.email };
      const analysis = await osintService.analyzeEmail(request);
      setResult(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze email");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Analysis</CardTitle>
        <CardDescription>
          Analyze email address for breaches, reputation, and more
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[rgb(var(--text-primary))] mb-1.5">
              Email Address
            </label>
            <Input
              {...register("email")}
              type="email"
              placeholder="user@example.com"
              className={errors.email ? "border-red-500" : ""}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">
                {errors.email.message}
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
                Analyzing...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Analyze Email
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
              {result.is_valid ? (
                <Badge variant="success">Valid</Badge>
              ) : (
                <Badge variant="danger">Invalid</Badge>
              )}
            </div>

            {/* Email Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <div className="flex items-center gap-2 mb-1">
                  {result.is_valid ? (
                    <CheckCircle2 className="h-4 w-4 text-primary-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                    Valid
                  </span>
                </div>
                <p className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                  {result.is_valid ? "Yes" : "No"}
                </p>
              </div>

              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Disposable
                </span>
                <p className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                  {result.is_disposable ? "Yes" : "No"}
                </p>
              </div>

              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Business Email
                </span>
                <p className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                  {result.is_business ? "Yes" : "No"}
                </p>
              </div>

              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Reputation Score
                </span>
                <p className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                  {result.reputation_score}/100
                </p>
              </div>
            </div>

            {/* Domain */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-3">
              <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                Domain
              </span>
              <p className="font-mono text-sm text-[rgb(var(--text-primary))]">
                {result.domain}
              </p>
            </div>

            {/* Breaches */}
            {result.breaches.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <h4 className="text-sm font-semibold text-red-600">
                    Data Breaches Found ({result.breaches.length})
                  </h4>
                </div>
                <div className="space-y-2">
                  {result.breaches.map((breach, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-950"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-semibold text-sm text-red-900 dark:text-red-100">
                            {breach.name}
                          </p>
                          <p className="text-xs text-red-600 dark:text-red-400">
                            {new Date(breach.date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {breach.data_classes.map((dataClass, i) => (
                          <Badge key={i} variant="danger" className="text-xs">
                            {dataClass}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Social Profiles */}
            {result.social_profiles.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-[rgb(var(--text-primary))] mb-3">
                  Social Profiles ({result.social_profiles.length})
                </h4>
                <div className="space-y-2">
                  {result.social_profiles.map((profile, idx) => (
                    <a
                      key={idx}
                      href={profile.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between rounded-lg border border-[rgb(var(--border))] p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {profile.platform}
                      </span>
                      <ExternalLink className="h-4 w-4 text-[rgb(var(--text-secondary))]" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
