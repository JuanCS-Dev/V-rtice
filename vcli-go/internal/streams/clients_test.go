package streams

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewStreamsClient(t *testing.T) {
	client := NewStreamsClient("http://test-streams:9092")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-streams:9092", client.endpoint)
}

// ============================================================================
// Topic Operations Tests
// ============================================================================

func TestListTopics_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/topics", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := TopicListResult{
			Topics: []TopicInfo{
				{Name: "security-events", Partitions: 10, ReplicationFactor: 3, MessageCount: 1500000},
				{Name: "threat-intel", Partitions: 5, ReplicationFactor: 2, MessageCount: 250000},
				{Name: "audit-logs", Partitions: 15, ReplicationFactor: 3, MessageCount: 5000000},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.ListTopics()

	require.NoError(t, err)
	assert.Len(t, result.Topics, 3)
	assert.Equal(t, "security-events", result.Topics[0].Name)
	assert.Equal(t, 10, result.Topics[0].Partitions)
	assert.Greater(t, result.Topics[0].MessageCount, int64(1000000))
}

func TestListTopics_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TopicListResult{Topics: []TopicInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.ListTopics()

	require.NoError(t, err)
	assert.Empty(t, result.Topics)
}

func TestCreateTopic_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/topics/create", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := TopicCreateResult{
			Topic:      "new-alerts",
			Partitions: 8,
			Status:     "created",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.CreateTopic(&TopicCreateRequest{
		Topic:      "new-alerts",
		Partitions: 8,
	})

	require.NoError(t, err)
	assert.Equal(t, "new-alerts", result.Topic)
	assert.Equal(t, 8, result.Partitions)
	assert.Equal(t, "created", result.Status)
}

func TestCreateTopic_Pending(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TopicCreateResult{
			Topic:      "pending-topic",
			Partitions: 3,
			Status:     "pending",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.CreateTopic(&TopicCreateRequest{
		Topic:      "pending-topic",
		Partitions: 3,
	})

	require.NoError(t, err)
	assert.Equal(t, "pending", result.Status)
}

func TestDescribeTopic_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/topics/describe", r.URL.Path)

		response := TopicDescribeResult{
			Topic:             "threat-intel",
			Partitions:        5,
			ReplicationFactor: 2,
			MessageCount:      250000,
			TotalSize:         "1.2 GB",
			PartitionDetails: []PartitionDetail{
				{ID: 0, Leader: 1, Offset: 50000, Lag: 0},
				{ID: 1, Leader: 2, Offset: 50000, Lag: 100},
				{ID: 2, Leader: 3, Offset: 50000, Lag: 0},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.DescribeTopic(&TopicDescribeRequest{Topic: "threat-intel"})

	require.NoError(t, err)
	assert.Equal(t, "threat-intel", result.Topic)
	assert.Equal(t, 5, result.Partitions)
	assert.Equal(t, "1.2 GB", result.TotalSize)
	assert.Len(t, result.PartitionDetails, 3)
	assert.Equal(t, int64(50000), result.PartitionDetails[0].Offset)
}

// ============================================================================
// Produce / Consume Tests
// ============================================================================

func TestProduce_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/produce", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		now := time.Now()
		response := ProduceResult{
			Topic:     "security-events",
			Partition: 7,
			Offset:    150234,
			Timestamp: now,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.Produce(&ProduceRequest{
		Topic:   "security-events",
		Key:     "alert-456",
		Value:   `{"type":"malware","severity":"high"}`,
		Headers: "correlation-id:xyz",
	})

	require.NoError(t, err)
	assert.Equal(t, "security-events", result.Topic)
	assert.Equal(t, 7, result.Partition)
	assert.Greater(t, result.Offset, int64(150000))
}

func TestConsume_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/consume", r.URL.Path)

		now := time.Now()
		response := ConsumeResult{
			MessageCount: 2,
			Messages: []Message{
				{
					Partition: 0,
					Offset:    100,
					Key:       "event-1",
					Value:     `{"type":"login","user":"admin"}`,
					Headers:   map[string]string{"source": "api-gateway"},
					Timestamp: now.Add(-5 * time.Minute),
				},
				{
					Partition: 0,
					Offset:    101,
					Key:       "event-2",
					Value:     `{"type":"logout","user":"admin"}`,
					Headers:   map[string]string{"source": "api-gateway"},
					Timestamp: now,
				},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.Consume(&ConsumeRequest{
		Topic:     "audit-logs",
		Consumer:  "security-analyzer",
		Partition: 0,
		Offset:    "earliest",
		Limit:     10,
	})

	require.NoError(t, err)
	assert.Equal(t, 2, result.MessageCount)
	assert.Len(t, result.Messages, 2)
	assert.Equal(t, "event-1", result.Messages[0].Key)
	assert.Equal(t, int64(100), result.Messages[0].Offset)
	assert.Contains(t, result.Messages[0].Value, "login")
}

func TestConsume_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ConsumeResult{
			MessageCount: 0,
			Messages:     []Message{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.Consume(&ConsumeRequest{
		Topic:  "empty-topic",
		Offset: "latest",
	})

	require.NoError(t, err)
	assert.Equal(t, 0, result.MessageCount)
	assert.Empty(t, result.Messages)
}

// ============================================================================
// Consumer Groups Tests
// ============================================================================

func TestListConsumers_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/consumers", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := ConsumerListResult{
			Consumers: []ConsumerInfo{
				{Group: "threat-processors", State: "stable", Members: 5, Lag: 1200},
				{Group: "audit-analyzers", State: "rebalancing", Members: 3, Lag: 450},
				{Group: "alert-handlers", State: "stable", Members: 8, Lag: 0},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.ListConsumers()

	require.NoError(t, err)
	assert.Len(t, result.Consumers, 3)
	assert.Equal(t, "threat-processors", result.Consumers[0].Group)
	assert.Equal(t, "stable", result.Consumers[0].State)
	assert.Equal(t, 5, result.Consumers[0].Members)
	assert.Greater(t, result.Consumers[0].Lag, int64(1000))
}

func TestListConsumers_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ConsumerListResult{Consumers: []ConsumerInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.ListConsumers()

	require.NoError(t, err)
	assert.Empty(t, result.Consumers)
}

func TestGetConsumerLag_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/consumers/lag", r.URL.Path)

		response := ConsumerLagResult{
			Consumer: "threat-processors",
			TotalLag: 1200,
			TopicLags: []TopicLag{
				{Topic: "security-events", Partition: 0, CurrentOffset: 100000, EndOffset: 100500, Lag: 500},
				{Topic: "security-events", Partition: 1, CurrentOffset: 100000, EndOffset: 100700, Lag: 700},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.GetConsumerLag(&ConsumerLagRequest{Consumer: "threat-processors"})

	require.NoError(t, err)
	assert.Equal(t, "threat-processors", result.Consumer)
	assert.Equal(t, int64(1200), result.TotalLag)
	assert.Len(t, result.TopicLags, 2)
	assert.Equal(t, "security-events", result.TopicLags[0].Topic)
	assert.Equal(t, int64(500), result.TopicLags[0].Lag)
}

func TestGetConsumerLag_NoLag(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ConsumerLagResult{
			Consumer:  "alert-handlers",
			TotalLag:  0,
			TopicLags: []TopicLag{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	result, err := client.GetConsumerLag(&ConsumerLagRequest{Consumer: "alert-handlers"})

	require.NoError(t, err)
	assert.Equal(t, int64(0), result.TotalLag)
	assert.Empty(t, result.TopicLags)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)

	t.Run("ListTopics", func(t *testing.T) {
		_, err := client.ListTopics()
		assert.Error(t, err)
	})

	t.Run("CreateTopic", func(t *testing.T) {
		_, err := client.CreateTopic(&TopicCreateRequest{})
		assert.Error(t, err)
	})

	t.Run("DescribeTopic", func(t *testing.T) {
		_, err := client.DescribeTopic(&TopicDescribeRequest{})
		assert.Error(t, err)
	})

	t.Run("Produce", func(t *testing.T) {
		_, err := client.Produce(&ProduceRequest{})
		assert.Error(t, err)
	})

	t.Run("Consume", func(t *testing.T) {
		_, err := client.Consume(&ConsumeRequest{})
		assert.Error(t, err)
	})

	t.Run("ListConsumers", func(t *testing.T) {
		_, err := client.ListConsumers()
		assert.Error(t, err)
	})

	t.Run("GetConsumerLag", func(t *testing.T) {
		_, err := client.GetConsumerLag(&ConsumerLagRequest{})
		assert.Error(t, err)
	})
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkListTopics(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(TopicListResult{Topics: []TopicInfo{}})
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.ListTopics()
	}
}

func BenchmarkProduce(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ProduceResult{Topic: "test", Offset: 1})
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	req := &ProduceRequest{Topic: "test", Value: "message"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Produce(req)
	}
}

func BenchmarkConsume(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ConsumeResult{MessageCount: 0})
	}))
	defer server.Close()

	client := NewStreamsClient(server.URL)
	req := &ConsumeRequest{Topic: "test", Offset: "latest"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Consume(req)
	}
}
