package vulnscan

type ScanRequest struct {
	Target string
	Full   bool
}

type ScanResult struct {
	ScanID          string
	Target          string
	Vulnerabilities []Vulnerability
}

type Vulnerability struct {
	CVE      string
	Title    string
	Severity string
	CVSS     float64
}

type ReportRequest struct {
	ScanID string
}

type ReportResult struct {
	ScanID    string
	Critical  int
	High      int
	Medium    int
	Low       int
	RiskScore float64
}

type StatusResult struct {
	Status              string
	ScansCompleted      int
	TotalVulnerabilities int
}
