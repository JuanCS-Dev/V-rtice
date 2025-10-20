package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/streaming"
	kafkapb "github.com/verticedev/vcli-go/api/grpc/kafka"
)

// Stream command flags
var (
	streamServer       string
	streamTopic        string
	streamTopics       []string
	streamConsumerGroup string
	streamOffset       int64
	streamPartition    int32
	streamEventTypes   []string
	streamSeverityMin  int32
	streamFieldFilters []string
	streamOutputFormat string
	streamPrettyPrint  bool
)

// streamCmd represents the stream command
var streamCmd = &cobra.Command{
	Use:   "stream",
	Short: "Stream real-time events",
	Long: `Stream real-time events from various sources.

The stream command provides unified access to real-time event streams
from different backends:
  - SSE (Server-Sent Events): HTTP-based event streaming
  - Kafka: High-throughput message streaming via gRPC proxy

Common Use Cases:
  - Monitor cytokine events from Active Immune Core
  - Watch hormone regulation signals
  - Track MAXIMUS decision events
  - Observe threat detection and response
  - Monitor system-wide coordination signals

Examples:
  # Stream cytokines from Kafka
  vcli stream kafka --topic immune.cytokines --event-type ameaca_detectada

  # Stream hormones with severity filter
  vcli stream kafka --topic immune.hormones --severity 7

  # Stream SSE events
  vcli stream sse --url http://localhost:8080/events

  # Stream multiple topics
  vcli stream kafka --topics immune.cytokines,immune.hormones`,
}

// ============================================================
// Kafka Streaming
// ============================================================

var streamKafkaCmd = &cobra.Command{
	Use:   "kafka",
	Short: "Stream messages from Kafka topics",
	Long: `Stream messages from Kafka topics via gRPC proxy.

The Kafka proxy provides a lightweight gRPC interface to Kafka topics,
avoiding heavyweight Kafka client dependencies in the CLI.

Offset Options:
  -1 = Latest (start from end, only new messages)
  -2 = Earliest (start from beginning)
  N  = Specific offset

Examples:
  # Stream cytokines (latest messages)
  vcli stream kafka --topic immune.cytokines --offset -1

  # Stream all messages from beginning
  vcli stream kafka --topic immune.cytokines --offset -2

  # Stream with event type filter
  vcli stream kafka --topic immune.cytokines \
    --event-type ameaca_detectada --event-type ameaca_neutralizada

  # Stream with severity filter
  vcli stream kafka --topic immune.hormones --severity 7

  # Stream from specific partition
  vcli stream kafka --topic immune.cytokines --partition 0

  # Consumer group (for parallel consumption)
  vcli stream kafka --topic immune.cytokines --consumer-group cli-monitor-1`,
	RunE: runStreamKafka,
}

func runStreamKafka(cmd *cobra.Command, args []string) error {
	// Validate inputs
	if streamTopic == "" && len(streamTopics) == 0 {
		return fmt.Errorf("--topic or --topics is required")
	}

	// Parse field filters
	fieldFilters := make(map[string]string)
	for _, f := range streamFieldFilters {
		parts := strings.SplitN(f, "=", 2)
		if len(parts) == 2 {
			fieldFilters[parts[0]] = parts[1]
		}
	}

	// Create Kafka client
	client, err := streaming.NewKafkaClient(streamServer)
	if err != nil {
		return fmt.Errorf("failed to create Kafka client: %w", err)
	}
	defer client.Close()

	// Setup context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Println("\n\n🛑 Stopping stream...")
		cancel()
	}()

	// Print stream info
	if streamTopic != "" {
		fmt.Printf("📡 Streaming from Kafka topic: %s\n", streamTopic)
	} else {
		fmt.Printf("📡 Streaming from Kafka topics: %s\n", strings.Join(streamTopics, ", "))
	}
	fmt.Printf("   Server: %s\n", streamServer)
	if streamConsumerGroup != "" {
		fmt.Printf("   Consumer Group: %s\n", streamConsumerGroup)
	}
	if len(streamEventTypes) > 0 {
		fmt.Printf("   Event Types: %s\n", strings.Join(streamEventTypes, ", "))
	}
	if streamSeverityMin > 0 {
		fmt.Printf("   Min Severity: %d\n", streamSeverityMin)
	}
	fmt.Println("   Press Ctrl+C to stop")

	// Message handler
	messageCount := 0
	handler := func(msg *kafkapb.KafkaMessage) error {
		messageCount++

		if streamOutputFormat == "json" {
			// JSON output
			data, _ := json.MarshalIndent(msg, "", "  ")
			fmt.Println(string(data))
		} else {
			// Pretty formatted output
			timestamp := msg.Timestamp.AsTime().Format("15:04:05.000")
			severityIcon := getSeverityIcon(msg.Severity)

			fmt.Printf("[%s] %s %s (partition:%d offset:%d)\n",
				timestamp,
				severityIcon,
				msg.EventType,
				msg.Partition,
				msg.Offset,
			)

			if streamPrettyPrint && msg.Payload != nil {
				payloadJSON, _ := json.MarshalIndent(msg.Payload, "  ", "  ")
				fmt.Printf("  Payload: %s\n", string(payloadJSON))
			}

			if msg.Key != "" {
				fmt.Printf("  Key: %s\n", msg.Key)
			}

			fmt.Println()
		}

		return nil
	}

	// Start streaming
	var streamErr error
	if streamTopic != "" {
		// Single topic
		streamErr = client.StreamTopic(
			ctx,
			streamTopic,
			streamConsumerGroup,
			streamOffset,
			streamPartition,
			streamEventTypes,
			streamSeverityMin,
			fieldFilters,
			handler,
		)
	} else {
		// Multiple topics
		streamErr = client.StreamTopics(
			ctx,
			streamTopics,
			streamConsumerGroup,
			streamOffset,
			streamEventTypes,
			streamSeverityMin,
			fieldFilters,
			handler,
		)
	}

	if streamErr != nil && streamErr != context.Canceled {
		return fmt.Errorf("stream error: %w", streamErr)
	}

	fmt.Printf("\n✅ Stream stopped. Total messages: %d\n", messageCount)
	return nil
}

// ============================================================
// SSE Streaming
// ============================================================

var streamSSECmd = &cobra.Command{
	Use:   "sse",
	Short: "Stream Server-Sent Events",
	Long: `Stream Server-Sent Events over HTTP.

SSE provides a simple HTTP-based event streaming mechanism,
commonly used for:
  - Real-time decision notifications
  - Status updates
  - Progress tracking
  - System alerts

Examples:
  # Stream governance events
  vcli stream sse --url http://localhost:8080/governance/stream

  # Stream with topic filter
  vcli stream sse --url http://localhost:8080/events \
    --topics decisions,alerts

  # Stream specific event types
  vcli stream sse --url http://localhost:8080/events \
    --event-type decision_pending --event-type decision_resolved`,
	RunE: runStreamSSE,
}

func runStreamSSE(cmd *cobra.Command, args []string) error {
	// Validate URL
	sseURL := streamServer
	if sseURL == "" {
		return fmt.Errorf("--url is required")
	}

	// Create SSE client
	client := streaming.NewSSEClient(sseURL, streamTopics)

	// Setup event filter if needed
	if len(streamEventTypes) > 0 {
		client.SetFilter(streaming.FilterByType(streamEventTypes...))
	}

	// Setup context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Println("\n\n🛑 Stopping stream...")
		cancel()
	}()

	// Subscribe
	eventCh, errorCh, err := client.Subscribe(ctx)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}
	defer client.Close()

	fmt.Printf("📡 Streaming SSE from: %s\n", sseURL)
	if len(streamTopics) > 0 {
		fmt.Printf("   Topics: %s\n", strings.Join(streamTopics, ", "))
	}
	if len(streamEventTypes) > 0 {
		fmt.Printf("   Event Types: %s\n", strings.Join(streamEventTypes, ", "))
	}
	fmt.Println("   Press Ctrl+C to stop")

	// Process events
	messageCount := 0
	for {
		select {
		case <-ctx.Done():
			fmt.Printf("\n✅ Stream stopped. Total events: %d\n", messageCount)
			return nil

		case event := <-eventCh:
			messageCount++

			if streamOutputFormat == "json" {
				data, _ := json.MarshalIndent(event, "", "  ")
				fmt.Println(string(data))
			} else {
				timestamp := event.Timestamp.Format("15:04:05.000")
				fmt.Printf("[%s] %s", timestamp, event.Type)

				if event.Topic != "" {
					fmt.Printf(" (topic:%s)", event.Topic)
				}
				if event.ID != "" {
					fmt.Printf(" [id:%s]", truncate(event.ID, 12))
				}
				fmt.Println()

				if streamPrettyPrint && len(event.Data) > 0 {
					dataJSON, _ := json.MarshalIndent(event.Data, "  ", "  ")
					fmt.Printf("  Data: %s\n", string(dataJSON))
				}
				fmt.Println()
			}

		case err := <-errorCh:
			fmt.Fprintf(os.Stderr, "⚠️  Error: %v\n", err)
		}
	}
}

// ============================================================
// Topic Info
// ============================================================

var streamTopicsCmd = &cobra.Command{
	Use:   "topics",
	Short: "List available Kafka topics",
	RunE:  runStreamTopics,
}

func runStreamTopics(cmd *cobra.Command, args []string) error {
	client, err := streaming.NewKafkaClient(streamServer)
	if err != nil {
		return fmt.Errorf("failed to create Kafka client: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	topics, err := client.ListTopics(ctx, "", false)
	if err != nil {
		return fmt.Errorf("failed to list topics: %w", err)
	}

	if len(topics) == 0 {
		fmt.Println("No topics found")
		return nil
	}

	fmt.Println("Available Kafka Topics:")
	for _, topic := range topics {
		fmt.Printf("  - %s\n", topic)
	}
	fmt.Printf("\nTotal: %d topics\n", len(topics))

	return nil
}

var streamTopicInfoCmd = &cobra.Command{
	Use:   "info <topic>",
	Short: "Get detailed topic information",
	Args:  cobra.ExactArgs(1),
	RunE:  runStreamTopicInfo,
}

func runStreamTopicInfo(cmd *cobra.Command, args []string) error {
	topic := args[0]

	client, err := streaming.NewKafkaClient(streamServer)
	if err != nil {
		return fmt.Errorf("failed to create Kafka client: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	info, err := client.GetTopicInfo(ctx, topic)
	if err != nil {
		return fmt.Errorf("failed to get topic info: %w", err)
	}

	fmt.Printf("Topic: %s\n", info.Topic)
	fmt.Printf("Partitions: %d\n", info.NumPartitions)
	fmt.Printf("Replication Factor: %d\n", info.ReplicationFactor)

	if len(info.Partitions) > 0 {
		fmt.Println("\nPartition Details:")
		for _, p := range info.Partitions {
			fmt.Printf("  Partition %d:\n", p.Partition)
			fmt.Printf("    Leader: %s\n", p.Leader)
			fmt.Printf("    Replicas: %s\n", strings.Join(p.Replicas, ", "))
			fmt.Printf("    In-Sync: %s\n", strings.Join(p.Isr, ", "))
			fmt.Printf("    Offset Range: %d - %d\n", p.EarliestOffset, p.LatestOffset)
			fmt.Printf("    Messages: %d\n", p.MessageCount)
		}
	}

	return nil
}

// ============================================================
// Init
// ============================================================

func init() {
	rootCmd.AddCommand(streamCmd)

	// Kafka streaming
	streamCmd.AddCommand(streamKafkaCmd)
	streamKafkaCmd.Flags().StringVar(&streamServer, "server", "localhost:50053", "Kafka proxy gRPC server")
	streamKafkaCmd.Flags().StringVar(&streamTopic, "topic", "", "Kafka topic to stream")
	streamKafkaCmd.Flags().StringSliceVar(&streamTopics, "topics", []string{}, "Multiple Kafka topics")
	streamKafkaCmd.Flags().StringVar(&streamConsumerGroup, "consumer-group", "", "Consumer group ID")
	streamKafkaCmd.Flags().Int64Var(&streamOffset, "offset", -1, "Start offset (-1=latest, -2=earliest)")
	streamKafkaCmd.Flags().Int32Var(&streamPartition, "partition", -1, "Specific partition (-1=all)")
	streamKafkaCmd.Flags().StringSliceVar(&streamEventTypes, "event-type", []string{}, "Filter by event types")
	streamKafkaCmd.Flags().Int32Var(&streamSeverityMin, "severity", 0, "Minimum severity level")
	streamKafkaCmd.Flags().StringSliceVar(&streamFieldFilters, "filter", []string{}, "Field filters (key=value)")
	streamKafkaCmd.Flags().StringVarP(&streamOutputFormat, "output", "o", "pretty", "Output format (json, pretty)")
	streamKafkaCmd.Flags().BoolVar(&streamPrettyPrint, "pretty", false, "Pretty print payloads")

	// SSE streaming
	streamCmd.AddCommand(streamSSECmd)
	streamSSECmd.Flags().StringVar(&streamServer, "url", "", "SSE endpoint URL (required)")
	streamSSECmd.Flags().StringSliceVar(&streamTopics, "topics", []string{}, "Topic filters")
	streamSSECmd.Flags().StringSliceVar(&streamEventTypes, "event-type", []string{}, "Event type filters")
	streamSSECmd.Flags().StringVarP(&streamOutputFormat, "output", "o", "pretty", "Output format (json, pretty)")
	streamSSECmd.Flags().BoolVar(&streamPrettyPrint, "pretty", false, "Pretty print event data")
	streamSSECmd.MarkFlagRequired("url")

	// Topic commands
	streamCmd.AddCommand(streamTopicsCmd)
	streamTopicsCmd.Flags().StringVar(&streamServer, "server", "localhost:50053", "Kafka proxy gRPC server")

	streamCmd.AddCommand(streamTopicInfoCmd)
	streamTopicInfoCmd.Flags().StringVar(&streamServer, "server", "localhost:50053", "Kafka proxy gRPC server")
}
