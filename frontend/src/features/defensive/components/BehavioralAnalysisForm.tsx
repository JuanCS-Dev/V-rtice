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
import { Loader2, Shield, Plus, Trash2, AlertTriangle } from "lucide-react";
import {
  defensiveService,
  type BehavioralAnalysisRequest,
  type BehavioralAnalysisResponse,
} from "@/services/api/defensiveService";

const eventSchema = z.object({
  timestamp: z.string().refine((val) => !isNaN(Date.parse(val)), {
    message: "Invalid timestamp",
  }),
  event_type: z.string().min(1, "Event type is required"),
  user_id: z.string().optional(),
  ip_address: z.string().optional(),
  endpoint: z.string().optional(),
  method: z.enum(["GET", "POST", "PUT", "DELETE", "PATCH"]).optional(),
  status_code: z.number().optional(),
  response_time: z.number().optional(),
});

const behavioralSchema = z.object({
  events: z.array(eventSchema).min(1, "At least one event is required"),
});

type BehavioralFormData = z.infer<typeof behavioralSchema>;

export function BehavioralAnalysisForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BehavioralAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<BehavioralFormData>({
    resolver: zodResolver(behavioralSchema),
    defaultValues: {
      events: [
        {
          timestamp: new Date().toISOString(),
          event_type: "login",
          ip_address: "",
          endpoint: "/api/auth/login",
          method: "POST",
        },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "events",
  });

  const onSubmit = async (data: BehavioralFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: BehavioralAnalysisRequest = {
        events: data.events.map((event) => ({
          ...event,
          status_code: event.status_code
            ? Number(event.status_code)
            : undefined,
          response_time: event.response_time
            ? Number(event.response_time)
            : undefined,
        })),
      };

      const analysis = await defensiveService.analyzeBehavior(request);
      setResult(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze behavior");
    } finally {
      setIsLoading(false);
    }
  };

  const addEvent = () => {
    append({
      timestamp: new Date().toISOString(),
      event_type: "",
      ip_address: "",
      endpoint: "",
      method: "GET",
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Behavioral Analysis</CardTitle>
        <CardDescription>
          Analyze user/system behavior patterns for anomalies
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Events */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-[rgb(var(--text-primary))]">
                Events ({fields.length})
              </label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addEvent}
                className="h-8"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Event
              </Button>
            </div>

            {fields.map((field, index) => (
              <div
                key={field.id}
                className="rounded-lg border border-[rgb(var(--border))] p-4 space-y-3"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-[rgb(var(--text-secondary))]">
                    Event #{index + 1}
                  </span>
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

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Input
                      {...register(`events.${index}.event_type`)}
                      placeholder="Event type (e.g., login)"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <Input
                      {...register(`events.${index}.ip_address`)}
                      placeholder="IP address"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <Input
                      {...register(`events.${index}.endpoint`)}
                      placeholder="Endpoint (e.g., /api/auth)"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <select
                      {...register(`events.${index}.method`)}
                      className="w-full rounded-lg border border-[rgb(var(--border))] px-3 py-2 text-sm"
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                      <option value="PATCH">PATCH</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}

            {errors.events && (
              <p className="text-xs text-red-600">{errors.events.message}</p>
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
                <Shield className="mr-2 h-4 w-4" />
                Analyze Behavior
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
              {result.is_anomaly ? (
                <Badge variant="danger">Anomaly Detected</Badge>
              ) : (
                <Badge variant="success">Normal Behavior</Badge>
              )}
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Confidence
                </span>
                <p className="text-2xl font-bold text-[rgb(var(--text-primary))]">
                  {(result.confidence * 100).toFixed(1)}%
                </p>
              </div>

              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Risk Score
                </span>
                <p
                  className={`text-2xl font-bold ${
                    result.risk_score > 70
                      ? "text-red-600"
                      : result.risk_score > 40
                        ? "text-amber-600"
                        : "text-primary-600"
                  }`}
                >
                  {result.risk_score}
                </p>
              </div>

              <div className="rounded-lg border border-[rgb(var(--border))] p-3">
                <span className="text-xs font-medium text-[rgb(var(--text-secondary))]">
                  Anomaly Type
                </span>
                <p className="text-sm font-semibold text-[rgb(var(--text-primary))] capitalize">
                  {result.anomaly_type || "N/A"}
                </p>
              </div>
            </div>

            {/* Explanation */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="text-sm font-semibold text-[rgb(var(--text-primary))] mb-2">
                Explanation
              </h4>
              <p className="text-sm text-[rgb(var(--text-secondary))]">
                {result.explanation}
              </p>
            </div>

            {/* Recommendations */}
            {result.recommendations.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-[rgb(var(--text-primary))] mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  Recommendations
                </h4>
                <div className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-primary-200 bg-primary-50 p-3 dark:border-primary-800 dark:bg-primary-950"
                    >
                      <p className="text-sm text-primary-900 dark:text-primary-100">
                        {rec}
                      </p>
                    </div>
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
