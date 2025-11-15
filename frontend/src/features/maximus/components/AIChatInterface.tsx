import { useState, useRef, useEffect } from "react";
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
import { Loader2, Send, Bot, User, Zap, Calendar } from "lucide-react";
import {
  maximusService,
  type AIChatRequest,
  type AIChatResponse,
} from "@/services/api/maximusService";

const chatSchema = z.object({
  message: z.string().min(1, "Message is required"),
});

type ChatFormData = z.infer<typeof chatSchema>;

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  tool_calls?: Array<{
    tool_name: string;
    parameters: Record<string, any>;
    result: any;
  }>;
  metadata?: {
    model: string;
    tokens_used: number;
    processing_time: number;
  };
}

export function AIChatInterface() {
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChatFormData>({
    resolver: zodResolver(chatSchema),
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const onSubmit = async (data: ChatFormData) => {
    const userMessage: ChatMessage = {
      role: "user",
      content: data.message,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    reset();

    try {
      const request: AIChatRequest = {
        message: data.message,
        conversation_id: conversationId,
      };

      const response: AIChatResponse = await maximusService.chat(request);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        tool_calls: response.tool_calls,
        metadata: response.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(response.conversation_id);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Error: ${err.response?.data?.detail || "Failed to send message"}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  return (
    <Card className="flex h-[calc(100vh-12rem)] flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Maximus AI Assistant</CardTitle>
            <CardDescription>
              AI-powered security analysis and investigation assistant
            </CardDescription>
          </div>
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearChat}>
              Clear Chat
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex flex-1 flex-col overflow-hidden">
        {/* Messages Container */}
        <div className="mb-4 flex-1 space-y-4 overflow-y-auto rounded-lg border border-[rgb(var(--border))] p-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <Bot className="h-16 w-16 text-[rgb(var(--text-tertiary))]" />
              <p className="mt-4 text-sm font-medium text-[rgb(var(--text-primary))]">
                Welcome to Maximus AI
              </p>
              <p className="mt-1 text-xs text-[rgb(var(--text-secondary))]">
                Ask me anything about security analysis, threat intelligence, or
                investigations
              </p>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.role === "assistant" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 shadow-sm">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}

              <div
                className={`max-w-[80%] space-y-2 rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-primary-500 text-white"
                    : "border border-[rgb(var(--border))] bg-[rgb(var(--card))]"
                }`}
              >
                <p
                  className={`text-sm ${
                    message.role === "user"
                      ? "text-white"
                      : "text-[rgb(var(--text-primary))]"
                  }`}
                >
                  {message.content}
                </p>

                {/* Tool Calls */}
                {message.tool_calls && message.tool_calls.length > 0 && (
                  <div className="mt-2 space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-medium text-[rgb(var(--text-secondary))]">
                      <Zap className="h-3.5 w-3.5" />
                      <span>Tools Used ({message.tool_calls.length})</span>
                    </div>
                    {message.tool_calls.map((tool, toolIdx) => (
                      <div
                        key={toolIdx}
                        className="rounded-md border border-primary-200 bg-primary-50 p-2 dark:border-primary-800 dark:bg-primary-950"
                      >
                        <Badge variant="default" className="mb-1">
                          {tool.tool_name}
                        </Badge>
                        <p className="font-mono text-xs text-primary-900 dark:text-primary-100">
                          {JSON.stringify(tool.parameters, null, 2)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Metadata */}
                {message.metadata && (
                  <div className="flex items-center gap-3 text-xs text-[rgb(var(--text-tertiary))]">
                    <span>{message.metadata.model}</span>
                    <span>•</span>
                    <span>{message.metadata.tokens_used} tokens</span>
                    <span>•</span>
                    <span>
                      {(message.metadata.processing_time / 1000).toFixed(2)}s
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-1.5 text-xs text-[rgb(var(--text-tertiary))]">
                  <Calendar className="h-3 w-3" />
                  <span>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              {message.role === "user" && (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-gray-500 to-gray-600 shadow-sm">
                  <User className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 shadow-sm">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="rounded-lg border border-[rgb(var(--border))] bg-[rgb(var(--card))] p-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary-600" />
                  <span className="text-sm text-[rgb(var(--text-secondary))]">
                    Thinking...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
          <Input
            {...register("message")}
            placeholder="Ask Maximus anything..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button type="submit" variant="primary" disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        {errors.message && (
          <p className="mt-1 text-xs text-red-600">{errors.message.message}</p>
        )}
      </CardContent>
    </Card>
  );
}
