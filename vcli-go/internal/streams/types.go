package streams

import "time"

// ============================================================================
// TOPIC MANAGEMENT
// ============================================================================

type TopicListResult struct {
	Topics []TopicInfo
}

type TopicInfo struct {
	Name              string
	Partitions        int
	ReplicationFactor int
	MessageCount      int64
}

type TopicCreateRequest struct {
	Topic      string
	Partitions int
}

type TopicCreateResult struct {
	Topic      string
	Partitions int
	Status     string
}

type TopicDescribeRequest struct {
	Topic string
}

type TopicDescribeResult struct {
	Topic             string
	Partitions        int
	ReplicationFactor int
	MessageCount      int64
	TotalSize         string
	PartitionDetails  []PartitionDetail
}

type PartitionDetail struct {
	ID     int
	Leader int
	Offset int64
	Lag    int64
}

// ============================================================================
// PRODUCE / CONSUME
// ============================================================================

type ProduceRequest struct {
	Topic   string
	Key     string
	Value   string
	Headers string
}

type ProduceResult struct {
	Topic     string
	Partition int
	Offset    int64
	Timestamp time.Time
}

type ConsumeRequest struct {
	Topic     string
	Consumer  string
	Partition int
	Offset    string
	Limit     int
}

type ConsumeResult struct {
	MessageCount int
	Messages     []Message
}

type Message struct {
	Partition int
	Offset    int64
	Key       string
	Value     string
	Headers   map[string]string
	Timestamp time.Time
}

// ============================================================================
// CONSUMER GROUPS
// ============================================================================

type ConsumerListResult struct {
	Consumers []ConsumerInfo
}

type ConsumerInfo struct {
	Group   string
	State   string
	Members int
	Lag     int64
}

type ConsumerLagRequest struct {
	Consumer string
}

type ConsumerLagResult struct {
	Consumer  string
	TotalLag  int64
	TopicLags []TopicLag
}

type TopicLag struct {
	Topic         string
	Partition     int
	CurrentOffset int64
	EndOffset     int64
	Lag           int64
}
