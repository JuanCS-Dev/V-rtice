package pipeline

// Tataca Ingestion
type IngestRequest struct {
	Source string
	Format string
}

type IngestResult struct {
	Source          string
	RecordsIngested int
	Status          string
}

// Seriema Graph
type GraphQueryRequest struct {
	Cypher string
}

type GraphQueryResult struct {
	Results []map[string]interface{}
}

type VisualizeRequest struct {
	Entity string
}

type VisualizeResult struct {
	Entity    string
	NodeCount int
	EdgeCount int
	GraphURL  string
}

// Command Bus
type CommandRequest struct {
	Topic   string
	Message string
}

type CommandResult struct {
	Topic     string
	MessageID string
	Status    string
}

type TopicListResult struct {
	Topics []TopicInfo
}

type TopicInfo struct {
	Name         string
	Subscribers  int
	MessageCount int
}

// Status
type StatusResult struct {
	Status         string
	TatacaIngested int
	SeriemaNodes   int
	BusMessages    int
}
