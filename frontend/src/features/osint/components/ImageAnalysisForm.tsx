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
  Image as ImageIcon,
  MapPin,
  Camera,
  Calendar,
  Upload,
} from "lucide-react";
import {
  osintService,
  type ImageAnalysisRequest,
  type ImageAnalysisResponse,
} from "@/services/api/osintService";

const imageSchema = z.object({
  image_url: z.string().url("Invalid URL").optional().or(z.literal("")),
  image_file: z.any().optional(),
});

type ImageFormData = z.infer<typeof imageSchema>;

export function ImageAnalysisForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ImageAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ImageFormData>({
    resolver: zodResolver(imageSchema),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const onSubmit = async (data: ImageFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      let request: ImageAnalysisRequest;

      if (data.image_file && data.image_file[0]) {
        // File upload
        const file = data.image_file[0];
        const reader = new FileReader();

        reader.onloadend = async () => {
          const base64 = reader.result as string;
          request = { image_data: base64 };

          try {
            const analysis = await osintService.analyzeImage(request);
            setResult(analysis);
          } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to analyze image");
          } finally {
            setIsLoading(false);
          }
        };

        reader.readAsDataURL(file);
      } else if (data.image_url) {
        // URL
        request = { image_url: data.image_url };
        const analysis = await osintService.analyzeImage(request);
        setResult(analysis);
        setIsLoading(false);
      } else {
        setError("Please provide an image URL or upload a file");
        setIsLoading(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze image");
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Image Analysis</CardTitle>
        <CardDescription>
          Extract metadata, geolocation, and perform reverse image search
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Image URL */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Image URL
            </label>
            <Input
              {...register("image_url")}
              placeholder="https://example.com/image.jpg"
            />
            {errors.image_url && (
              <p className="mt-1 text-xs text-red-600">
                {errors.image_url.message}
              </p>
            )}
          </div>

          {/* OR Divider */}
          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-[rgb(var(--border))]" />
            <span className="text-xs font-medium text-[rgb(var(--text-tertiary))]">
              OR
            </span>
            <div className="h-px flex-1 bg-[rgb(var(--border))]" />
          </div>

          {/* File Upload */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Upload Image
            </label>
            <div className="relative">
              <input
                {...register("image_file")}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="block w-full rounded-lg border border-[rgb(var(--border))] text-sm file:mr-4 file:rounded-l-lg file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-950 dark:file:text-primary-300"
              />
            </div>
          </div>

          {/* Preview */}
          {previewUrl && (
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <img
                src={previewUrl}
                alt="Preview"
                className="max-h-64 w-auto rounded-lg object-contain"
              />
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
                Analyzing...
              </>
            ) : (
              <>
                <ImageIcon className="mr-2 h-4 w-4" />
                Analyze Image
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
            <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
              Analysis Results
            </h3>

            {/* Metadata */}
            {result.metadata && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  <Camera className="h-4 w-4 text-primary-600" />
                  Image Metadata
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  {result.metadata.camera && (
                    <div>
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Camera
                      </span>
                      <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.metadata.camera}
                      </p>
                    </div>
                  )}
                  {result.metadata.date_taken && (
                    <div>
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Date Taken
                      </span>
                      <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {new Date(result.metadata.date_taken).toLocaleString()}
                      </p>
                    </div>
                  )}
                  {result.metadata.dimensions && (
                    <div>
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Dimensions
                      </span>
                      <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.metadata.dimensions}
                      </p>
                    </div>
                  )}
                  {result.metadata.file_size && (
                    <div>
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        File Size
                      </span>
                      <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.metadata.file_size}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Geolocation */}
            {result.location && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  <MapPin className="h-4 w-4 text-primary-600" />
                  Geolocation Data
                </h4>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-[rgb(var(--text-secondary))]">
                      Coordinates
                    </span>
                    <p className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                      {result.location.latitude}, {result.location.longitude}
                    </p>
                  </div>
                  {result.location.address && (
                    <div>
                      <span className="text-xs text-[rgb(var(--text-secondary))]">
                        Address
                      </span>
                      <p className="text-sm font-medium text-[rgb(var(--text-primary))]">
                        {result.location.address}
                      </p>
                    </div>
                  )}
                  <a
                    href={`https://www.google.com/maps?q=${result.location.latitude},${result.location.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400"
                  >
                    View on Google Maps
                  </a>
                </div>
              </div>
            )}

            {/* Reverse Search */}
            {result.reverse_search_results &&
              result.reverse_search_results.length > 0 && (
                <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                  <h4 className="mb-3 text-sm font-semibold text-[rgb(var(--text-primary))]">
                    Reverse Image Search ({result.reverse_search_results.length}{" "}
                    matches)
                  </h4>
                  <div className="space-y-2">
                    {result.reverse_search_results.map((match, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-primary-200 bg-primary-50 p-3 dark:border-primary-800 dark:bg-primary-950"
                      >
                        <a
                          href={match.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-sm text-primary-900 hover:underline dark:text-primary-100"
                        >
                          {match.title}
                        </a>
                        <p className="mt-1 text-xs text-primary-700 dark:text-primary-300">
                          {match.source}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Labels/Tags */}
            {result.labels && result.labels.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  Detected Labels
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {result.labels.map((label, idx) => (
                    <Badge key={idx} variant="default">
                      {label}
                    </Badge>
                  ))}
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
