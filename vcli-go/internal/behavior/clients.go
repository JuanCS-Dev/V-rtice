package behavior

import (
	"github.com/verticedev/vcli-go/internal/config"
	"context"
	"net/http"
	"time"
)

type BaseClient struct {
	endpoint   string
	httpClient *http.Client
	ctx        context.Context
}

func newBaseClient(endpoint string) *BaseClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("behavior")
	}

	return &BaseClient{
		endpoint: endpoint,
		httpClient: &http.Client{Timeout: 30 * time.Second},
		ctx:      context.Background(),
	}
}

type AnalysisClient struct {
	*BaseClient
}

func NewAnalysisClient(endpoint string) *AnalysisClient {
	return &AnalysisClient{BaseClient: newBaseClient(endpoint)}
}

func (c *AnalysisClient) Analyze(req *AnalyzeRequest) (*AnalyzeResult, error) {
	return &AnalyzeResult{
		User:         req.User,
		Timerange:    req.Timerange,
		AnomalyScore: 0.65,
		RiskLevel:    "medium",
		Anomalies: []Anomaly{
			{Description: "Unusual login time", Severity: 5, Confidence: 0.78, Timestamp: time.Now()},
			{Description: "Access from new location", Severity: 6, Confidence: 0.85, Timestamp: time.Now()},
		},
	}, nil
}

type BASClient struct {
	*BaseClient
}

func NewBASClient(endpoint string) *BASClient {
	return &BASClient{BaseClient: newBaseClient(endpoint)}
}

func (c *BASClient) DetectAnomaly(req *BASDetectRequest) (*BASDetectResult, error) {
	return &BASDetectResult{
		Entity: req.Entity,
		Status: "anomalies_detected",
		Anomalies: []BASAnomaly{
			{Type: "CPU spike", Severity: 7, Confidence: 0.92, Timestamp: time.Now()},
			{Type: "Unusual network pattern", Severity: 6, Confidence: 0.81, Timestamp: time.Now()},
		},
	}, nil
}

type MAVClient struct {
	*BaseClient
}

func NewMAVClient(endpoint string) *MAVClient {
	return &MAVClient{BaseClient: newBaseClient(endpoint)}
}

func (c *MAVClient) Scan(req *MAVScanRequest) (*MAVScanResult, error) {
	return &MAVScanResult{
		Network:      req.Network,
		HostsScanned: 254,
		Vectors: []MAVector{
			{Type: "Port scanning", Source: "10.0.0.15", Severity: 6},
			{Type: "Brute force attempt", Source: "10.0.0.42", Severity: 8},
		},
	}, nil
}

type TrafficClient struct {
	*BaseClient
}

func NewTrafficClient(endpoint string) *TrafficClient {
	return &TrafficClient{BaseClient: newBaseClient(endpoint)}
}

func (c *TrafficClient) Analyze(req *TrafficAnalyzeRequest) (*TrafficAnalyzeResult, error) {
	return &TrafficAnalyzeResult{
		PacketsAnalyzed: 125430,
		FlowsIdentified: 1247,
		AnomalousFlows: []AnomalousFlow{
			{Source: "192.168.1.50", Destination: "8.8.8.8", Protocol: "DNS", AnomalyType: "DNS tunneling", Severity: 8},
			{Source: "192.168.1.100", Destination: "external-c2.com", Protocol: "HTTPS", AnomalyType: "C2 communication", Severity: 9},
		},
	}, nil
}

type FabricClient struct {
	*BaseClient
}

func NewFabricClient(endpoint string) *FabricClient {
	return &FabricClient{BaseClient: newBaseClient(endpoint)}
}

func (c *FabricClient) GetStatus() (*FabricStatus, error) {
	return &FabricStatus{
		Components: []FabricComponent{
			{Name: "Fabric Core", Status: "active", ActiveRules: 342, EventsPerSecond: 1250},
			{Name: "Fabric Analysis", Status: "active", ActiveRules: 128, EventsPerSecond: 850},
			{Name: "Fabric Response", Status: "active", ActiveRules: 67, EventsPerSecond: 420},
		},
	}, nil
}
