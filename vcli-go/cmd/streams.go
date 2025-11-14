package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/streams"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for streams commands
var (
	streamsServer    string
	streamsTopic     string
	streamsConsumer  string
	streamsPartition int
	streamsOffset    string
	streamsLimit     int
	streamsFormat    string
	streamsKey       string
	streamsValue     string
	streamsHeaders   string
)

// streamsCmd represents the Kafka streams command
var streamsCmd = &cobra.Command{
	Use:   "streams",
	Short: "Kafka event streaming operations",
	Long: `Manage Kafka event streams for real-time data processing and event-driven architecture.

The streams system provides Kafka integration for publishing events, consuming streams,
managing topics, and monitoring consumer groups across the Vértice ecosystem.

Components:
  topic        - Kafka topic management
  produce      - Produce messages to topics
  consume      - Consume messages from topics
  consumer     - Consumer group management

Examples:
  # List topics
  vcli streams topic list

  # Produce event
  vcli streams produce --topic events --key user123 --value '{"action":"login"}'

  # Consume stream
  vcli streams consume --topic events --consumer vcli-consumer

  # Check consumer lag
  vcli streams consumer lag --consumer threat-detection
`,
}

// ============================================================================
// TOPIC MANAGEMENT
// ============================================================================

var streamsTopicCmd = &cobra.Command{
	Use:   "topic",
	Short: "Kafka topic operations",
	Long:  `Manage Kafka topics (list, create, describe, delete).`,
}

var streamsTopicListCmd = &cobra.Command{
	Use:   "list",
	Short: "List Kafka topics",
	Long:  `List all Kafka topics in the cluster.`,
	Example: `  # List all topics
  vcli streams topic list`,
	RunE: runStreamsTopicList,
}

func runStreamsTopicList(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	result, err := client.ListTopics()
	if err != nil {
		return fmt.Errorf("failed to list topics: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📋 Kafka Topics"))

	if len(result.Topics) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nTOPIC\tPARTITIONS\tREPLICATION\tMESSAGES\n")
		fmt.Fprintf(w, "-----\t----------\t-----------\t--------\n")
		for _, topic := range result.Topics {
			fmt.Fprintf(w, "%s\t%d\t%d\t%d\n",
				topic.Name,
				topic.Partitions,
				topic.ReplicationFactor,
				topic.MessageCount,
			)
		}
		w.Flush()
	}

	return nil
}

var streamsTopicCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create Kafka topic",
	Long:  `Create a new Kafka topic with specified configuration.`,
	Example: `  # Create topic
  vcli streams topic create --topic new-events --partition 3`,
	RunE: runStreamsTopicCreate,
}

func runStreamsTopicCreate(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	req := &streams.TopicCreateRequest{
		Topic:      streamsTopic,
		Partitions: streamsPartition,
	}

	result, err := client.CreateTopic(req)
	if err != nil {
		return fmt.Errorf("failed to create topic: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Topic Created"))
	fmt.Printf("\nTopic: %s\n", result.Topic)
	fmt.Printf("Partitions: %d\n", result.Partitions)
	fmt.Printf("Status: %s\n", getStatusIcon(result.Status))

	return nil
}

var streamsTopicDescribeCmd = &cobra.Command{
	Use:   "describe",
	Short: "Describe Kafka topic",
	Long:  `Get detailed information about a Kafka topic.`,
	Example: `  # Describe topic
  vcli streams topic describe --topic events`,
	RunE: runStreamsTopicDescribe,
}

func runStreamsTopicDescribe(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	req := &streams.TopicDescribeRequest{Topic: streamsTopic}

	result, err := client.DescribeTopic(req)
	if err != nil {
		return fmt.Errorf("failed to describe topic: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📊 Topic Details"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTopic:\t%s\n", result.Topic)
	fmt.Fprintf(w, "Partitions:\t%d\n", result.Partitions)
	fmt.Fprintf(w, "Replication Factor:\t%d\n", result.ReplicationFactor)
	fmt.Fprintf(w, "Message Count:\t%d\n", result.MessageCount)
	fmt.Fprintf(w, "Total Size:\t%s\n", result.TotalSize)
	w.Flush()

	if len(result.PartitionDetails) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Partition Details"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "PARTITION\tLEADER\tOFFSET\tLAG\n")
		fmt.Fprintf(w, "---------\t------\t------\t---\n")
		for _, part := range result.PartitionDetails {
			fmt.Fprintf(w, "%d\t%d\t%d\t%d\n",
				part.ID,
				part.Leader,
				part.Offset,
				part.Lag,
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// PRODUCE MESSAGES
// ============================================================================

var streamsProduceCmd = &cobra.Command{
	Use:   "produce",
	Short: "Produce message to topic",
	Long: `Publish a message to a Kafka topic.

Messages can include key, value, and custom headers.`,
	Example: `  # Produce simple message
  vcli streams produce --topic events --value '{"event":"user_login"}'

  # Produce with key
  vcli streams produce --topic events --key user123 --value '{"action":"login"}'

  # Produce with headers
  vcli streams produce --topic events --key user123 --value '{"data":"test"}' --headers "source:vcli,version:1.0"`,
	RunE: runStreamsProduce,
}

func runStreamsProduce(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	req := &streams.ProduceRequest{
		Topic:   streamsTopic,
		Key:     streamsKey,
		Value:   streamsValue,
		Headers: streamsHeaders,
	}

	result, err := client.Produce(req)
	if err != nil {
		return fmt.Errorf("failed to produce message: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Message Produced"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTopic:\t%s\n", result.Topic)
	fmt.Fprintf(w, "Partition:\t%d\n", result.Partition)
	fmt.Fprintf(w, "Offset:\t%d\n", result.Offset)
	fmt.Fprintf(w, "Timestamp:\t%s\n", result.Timestamp.Format("2006-01-02 15:04:05"))
	w.Flush()

	return nil
}

// ============================================================================
// CONSUME MESSAGES
// ============================================================================

var streamsConsumeCmd = &cobra.Command{
	Use:   "consume",
	Short: "Consume messages from topic",
	Long: `Consume and display messages from a Kafka topic.

Can consume from specific partition/offset or use consumer group.`,
	Example: `  # Consume with consumer group
  vcli streams consume --topic events --consumer vcli-consumer

  # Consume from specific offset
  vcli streams consume --topic events --partition 0 --offset earliest --limit 10

  # Consume latest messages
  vcli streams consume --topic events --offset latest --limit 5`,
	RunE: runStreamsConsume,
}

func runStreamsConsume(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	req := &streams.ConsumeRequest{
		Topic:     streamsTopic,
		Consumer:  streamsConsumer,
		Partition: streamsPartition,
		Offset:    streamsOffset,
		Limit:     streamsLimit,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("📥 Consuming messages..."))

	result, err := client.Consume(req)
	if err != nil {
		return fmt.Errorf("failed to consume messages: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("\n%s (%d messages)\n", styles.Success.Render("Messages"), result.MessageCount)

	if len(result.Messages) > 0 {
		for i, msg := range result.Messages {
			fmt.Printf("\n%s Message #%d %s\n",
				styles.Info.Render("═════"),
				i+1,
				styles.Info.Render("═════"),
			)
			fmt.Printf("Partition: %d | Offset: %d | Timestamp: %s\n",
				msg.Partition,
				msg.Offset,
				msg.Timestamp.Format("15:04:05"),
			)
			if msg.Key != "" {
				fmt.Printf("Key: %s\n", msg.Key)
			}
			fmt.Printf("Value: %s\n", msg.Value)
			if len(msg.Headers) > 0 {
				fmt.Printf("Headers: %v\n", msg.Headers)
			}
		}
	}

	return nil
}

// ============================================================================
// CONSUMER GROUP MANAGEMENT
// ============================================================================

var streamsConsumerCmd = &cobra.Command{
	Use:   "consumer",
	Short: "Consumer group operations",
	Long:  `Manage Kafka consumer groups and monitor lag.`,
}

var streamsConsumerListCmd = &cobra.Command{
	Use:   "list",
	Short: "List consumer groups",
	Long:  `List all Kafka consumer groups.`,
	Example: `  # List consumer groups
  vcli streams consumer list`,
	RunE: runStreamsConsumerList,
}

func runStreamsConsumerList(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	result, err := client.ListConsumers()
	if err != nil {
		return fmt.Errorf("failed to list consumers: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("👥 Consumer Groups"))

	if len(result.Consumers) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nCONSUMER GROUP\tSTATE\tMEMBERS\tLAG\n")
		fmt.Fprintf(w, "--------------\t-----\t-------\t---\n")
		for _, consumer := range result.Consumers {
			fmt.Fprintf(w, "%s\t%s\t%d\t%d\n",
				consumer.Group,
				consumer.State,
				consumer.Members,
				consumer.Lag,
			)
		}
		w.Flush()
	}

	return nil
}

var streamsConsumerLagCmd = &cobra.Command{
	Use:   "lag",
	Short: "Check consumer lag",
	Long:  `Check lag for a specific consumer group.`,
	Example: `  # Check consumer lag
  vcli streams consumer lag --consumer threat-detection`,
	RunE: runStreamsConsumerLag,
}

func runStreamsConsumerLag(cmd *cobra.Command, args []string) error {
	client := streams.NewStreamsClient(getStreamsServer())

	req := &streams.ConsumerLagRequest{Consumer: streamsConsumer}

	result, err := client.GetConsumerLag(req)
	if err != nil {
		return fmt.Errorf("failed to get consumer lag: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📊 Consumer Lag"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nConsumer:\t%s\n", result.Consumer)
	fmt.Fprintf(w, "Total Lag:\t%d\n", result.TotalLag)
	w.Flush()

	if len(result.TopicLags) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Per-Topic Lag"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "TOPIC\tPARTITION\tCURRENT\tEND\tLAG\n")
		fmt.Fprintf(w, "-----\t---------\t-------\t---\t---\n")
		for _, lag := range result.TopicLags {
			fmt.Fprintf(w, "%s\t%d\t%d\t%d\t%d\n",
				lag.Topic,
				lag.Partition,
				lag.CurrentOffset,
				lag.EndOffset,
				lag.Lag,
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getStreamsServer() string {
	if streamsServer != "" {
		return streamsServer
	}

	return config.GetEndpoint("streams")
}
