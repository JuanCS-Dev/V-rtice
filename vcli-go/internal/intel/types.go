package intel

import "time"

// ============================================================================
// GOOGLE OSINT
// ============================================================================

type GoogleSearchRequest struct {
	Query string
	Depth string
}

type GoogleSearchResult struct {
	Query          string
	TotalResults   int
	ProcessingTime float64
	Results        []GoogleResult
	Exposures      []GoogleExposure
}

type GoogleResult struct {
	Title    string
	URL      string
	Snippet  string
	FileType string
}

type GoogleExposure struct {
	Type        string
	Description string
	URL         string
}

type GoogleDorkRequest struct {
	Dork string
}

type GoogleDorkResult struct {
	Dork     string
	Findings []GoogleDorkFinding
}

type GoogleDorkFinding struct {
	URL         string
	RiskLevel   string
	Description string
}

// ============================================================================
// IP INTELLIGENCE
// ============================================================================

type IPLookupRequest struct {
	IP     string
	Format string
}

type IPLookupResult struct {
	IP               string
	Country          string
	CountryCode      string
	City             string
	Region           string
	ISP              string
	ASN              string
	Reputation       string
	ThreatScore      int
	ThreatIndicators []string
}

type IPGeoRequest struct {
	IP string
}

type IPGeoResult struct {
	IP        string
	Latitude  float64
	Longitude float64
	Country   string
	Region    string
	City      string
	Timezone  string
}

// ============================================================================
// SINESP (Brazil)
// ============================================================================

type SinespPlateRequest struct {
	Plate string
}

type SinespPlateResult struct {
	Plate  string
	State  string
	City   string
	Make   string
	Model  string
	Year   int
	Color  string
	Status string
	Alerts []string
}

type SinespDocumentRequest struct {
	Document string
}

type SinespDocumentResult struct {
	Document string
	Name     string
	Status   string
	Alerts   []string
}

// ============================================================================
// SSL MONITORING
// ============================================================================

type SSLCheckRequest struct {
	Domain string
	Format string
}

type SSLCheckResult struct {
	Domain          string
	Status          string
	Issuer          string
	ValidFrom       time.Time
	ValidUntil      time.Time
	DaysUntilExpiry int
	Protocol        string
	Cipher          string
	Warnings        []string
	Vulnerabilities []string
}

type SSLMonitorRequest struct {
	Domain string
}

type SSLMonitorResult struct {
	Domain        string
	MonitorID     string
	CheckInterval string
	Status        string
}

// ============================================================================
// NARRATIVE ANALYSIS
// ============================================================================

type NarrativeAnalyzeRequest struct {
	Text string
}

type NarrativeAnalyzeResult struct {
	ManipulationScore float64
	CredibilityScore  float64
	Sentiment         string
	Language          string
	Techniques        []ManipulationTechnique
	Claims            []NarrativeClaim
}

type ManipulationTechnique struct {
	Name        string
	Description string
	Confidence  float64
}

type NarrativeClaim struct {
	Text       string
	Veracity   string
	Confidence float64
}

type NarrativeDetectRequest struct {
	Text string
}

type NarrativeDetectResult struct {
	Status     string
	Confidence float64
	RiskLevel  string
	Indicators []string
}
