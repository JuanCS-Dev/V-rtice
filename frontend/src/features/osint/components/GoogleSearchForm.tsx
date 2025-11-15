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
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Badge,
} from "@/components/ui";
import {
  Loader2,
  Search,
  ExternalLink,
  Image as ImageIcon,
  Calendar,
} from "lucide-react";
import {
  osintService,
  type GoogleSearchRequest,
  type GoogleSearchResponse,
} from "@/services/api/osintService";

const searchSchema = z.object({
  query: z.string().min(1, "Search query is required"),
  max_results: z.number().min(1).max(100).optional(),
});

type SearchFormData = z.infer<typeof searchSchema>;

export function GoogleSearchForm() {
  const [activeTab, setActiveTab] = useState<
    "web" | "news" | "images" | "videos" | "scholar"
  >("web");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<GoogleSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      max_results: 10,
    },
  });

  const onSubmit = async (data: SearchFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: GoogleSearchRequest = {
        query: data.query,
        search_type: activeTab,
        max_results: data.max_results,
      };

      const searchResult = await osintService.googleSearch(request);
      setResult(searchResult);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to perform search");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Google OSINT Search</CardTitle>
        <CardDescription>
          Advanced Google searching across multiple content types
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList className="mb-4">
            <TabsTrigger value="web">Web</TabsTrigger>
            <TabsTrigger value="news">News</TabsTrigger>
            <TabsTrigger value="images">Images</TabsTrigger>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="scholar">Scholar</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Query Input */}
              <div>
                <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
                  Search Query
                </label>
                <Input
                  {...register("query")}
                  placeholder={`Search ${activeTab}...`}
                  className="font-mono"
                />
                {errors.query && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.query.message}
                  </p>
                )}
              </div>

              {/* Max Results */}
              <div>
                <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
                  Max Results
                </label>
                <Input
                  {...register("max_results", { valueAsNumber: true })}
                  type="number"
                  min={1}
                  max={100}
                  defaultValue={10}
                />
                {errors.max_results && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.max_results.message}
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
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search{" "}
                    {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                  </>
                )}
              </Button>
            </form>
          </TabsContent>
        </Tabs>

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
                Search Results ({result.total_results.toLocaleString()} found)
              </h3>
              <Badge variant="default">{result.search_type}</Badge>
            </div>

            {/* Results List */}
            <div className="space-y-3">
              {result.results.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-[rgb(var(--border))] p-4 transition-all hover:border-primary-500 hover:shadow-sm"
                >
                  {/* Title & Link */}
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-sm text-primary-600 hover:underline dark:text-primary-400"
                    >
                      {item.title}
                    </a>
                    <ExternalLink className="h-4 w-4 flex-shrink-0 text-[rgb(var(--text-tertiary))]" />
                  </div>

                  {/* URL */}
                  <p className="mb-2 truncate font-mono text-xs text-primary-600 dark:text-primary-400">
                    {item.url}
                  </p>

                  {/* Snippet */}
                  <p className="text-sm text-[rgb(var(--text-secondary))]">
                    {item.snippet}
                  </p>

                  {/* Thumbnail for images/videos */}
                  {item.thumbnail && (
                    <div className="mt-3">
                      <img
                        src={item.thumbnail}
                        alt={item.title}
                        className="h-20 w-auto rounded-lg border border-[rgb(var(--border))] object-cover"
                        loading="lazy"
                      />
                    </div>
                  )}

                  {/* Published date for news */}
                  {item.published_date && (
                    <div className="mt-2 flex items-center gap-1.5 text-xs text-[rgb(var(--text-tertiary))]">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>
                        {new Date(item.published_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}

                  {/* Source for news/scholar */}
                  {item.source && (
                    <div className="mt-2">
                      <Badge variant="default">{item.source}</Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Empty State */}
            {result.results.length === 0 && (
              <div className="rounded-lg border border-[rgb(var(--border))] bg-[rgb(var(--card))] p-8 text-center">
                <Search className="mx-auto h-12 w-12 text-[rgb(var(--text-tertiary))]" />
                <p className="mt-3 text-sm font-medium text-[rgb(var(--text-primary))]">
                  No results found
                </p>
                <p className="mt-1 text-xs text-[rgb(var(--text-secondary))]">
                  Try adjusting your search query
                </p>
              </div>
            )}

            {/* Metadata */}
            <div className="flex items-center gap-2 text-xs text-[rgb(var(--text-tertiary))]">
              <Calendar className="h-3.5 w-3.5" />
              <span>
                Searched at {new Date(result.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
