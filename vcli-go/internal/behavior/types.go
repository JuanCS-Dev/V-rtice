package behavior

import "time"

type AnalyzeRequest struct {
	User      string
	Timerange string
	Threshold float64
}

type AnalyzeResult struct {
	User         string
	Timerange    string
	AnomalyScore float64
	RiskLevel    string
	Anomalies    []Anomaly
}

type Anomaly struct {
	Description string
	Severity    int
	Confidence  float64
	Timestamp   time.Time
}

type BASDetectRequest struct {
	Entity string
	Mode   string
}

type BASDetectResult struct {
	Entity    string
	Status    string
	Anomalies []BASAnomaly
}

type BASAnomaly struct {
	Type       string
	Severity   int
	Confidence float64
	Timestamp  time.Time
}

type MAVScanRequest struct {
	Network string
	Mode    string
}

type MAVScanResult struct {
	Network      string
	HostsScanned int
	Vectors      []MAVector
}

type MAVector struct {
	Type     string
	Source   string
	Severity int
}

type TrafficAnalyzeRequest struct {
	PCAPPath string
	Mode     string
}

type TrafficAnalyzeResult struct {
	PacketsAnalyzed int
	FlowsIdentified int
	AnomalousFlows  []AnomalousFlow
}

type AnomalousFlow struct {
	Source      string
	Destination string
	Protocol    string
	AnomalyType string
	Severity    int
}

type FabricStatus struct {
	Components []FabricComponent
}

type FabricComponent struct {
	Name            string
	Status          string
	ActiveRules     int
	EventsPerSecond int
}
