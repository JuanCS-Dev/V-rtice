package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/intel"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for intel commands
var (
	intelServer     string
	intelQuery      string
	intelIP         string
	intelDomain     string
	intelPlate      string
	intelDocument   string
	intelText       string
	intelDepth      string
	intelFormat     string
	intelOutputFile string
)

// intopsCmd represents the OSINT and intelligence gathering command
var intopsCmd = &cobra.Command{
	Use:   "intops",
	Short: "Intelligence operations and OSINT tools",
	Long: `Perform OSINT operations, intelligence gathering, and information analysis.

The intel system provides capabilities for collecting, analyzing, and correlating
intelligence from multiple sources including Google OSINT, IP intelligence,
Brazilian government databases (SINESP), SSL/TLS monitoring, and narrative analysis.

Components:
  google       - Google OSINT operations
  ip           - IP intelligence and geolocation
  sinesp       - SINESP Brazil government database
  ssl          - SSL/TLS certificate monitoring
  narrative    - Narrative analysis and manipulation detection

Examples:
  # Google OSINT search
  vcli intops google search --query "site:example.com filetype:pdf"

  # IP intelligence lookup
  vcli intops ip lookup --ip 8.8.8.8

  # SINESP vehicle plate lookup
  vcli intops sinesp plate --plate ABC1234

  # SSL certificate monitoring
  vcli intops ssl check --domain example.com

  # Narrative manipulation detection
  vcli intops narrative analyze --text "suspicious narrative"
`,
}

// ============================================================================
// GOOGLE OSINT
// ============================================================================

var intelGoogleCmd = &cobra.Command{
	Use:   "google",
	Short: "Google OSINT operations",
	Long:  `Perform OSINT operations using Google search capabilities.`,
}

var intelGoogleSearchCmd = &cobra.Command{
	Use:   "search",
	Short: "Perform Google OSINT search",
	Long: `Search using advanced Google operators for OSINT purposes.

Supports advanced search operators like site:, filetype:, inurl:, intitle:, etc.`,
	Example: `  # Search for PDFs on a domain
  vcli intops google search --query "site:example.com filetype:pdf"

  # Search for exposed credentials
  vcli intops google search --query "site:pastebin.com password"

  # Deep search with specific depth
  vcli intops google search --query "company secrets" --depth deep`,
	RunE: runIntelGoogleSearch,
}

func runIntelGoogleSearch(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.GoogleSearchRequest{
		Query: intelQuery,
		Depth: intelDepth,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔍 Performing Google OSINT search..."))

	result, err := client.SearchGoogle(req)
	if err != nil {
		return fmt.Errorf("failed to perform Google search: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Google OSINT Search Complete"))
	fmt.Printf("\nQuery: %s\n", result.Query)
	fmt.Printf("Results found: %d\n", result.TotalResults)
	fmt.Printf("Processing time: %.2fs\n", result.ProcessingTime)

	if len(result.Results) > 0 {
		fmt.Printf("\n%s:\n", styles.Success.Render("Top Results"))
		for i, r := range result.Results {
			fmt.Printf("\n%d. %s\n", i+1, r.Title)
			fmt.Printf("   URL: %s\n", r.URL)
			fmt.Printf("   Snippet: %s\n", r.Snippet)
			if r.FileType != "" {
				fmt.Printf("   Type: %s\n", r.FileType)
			}
		}
	}

	if len(result.Exposures) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("⚠️  Potential Exposures"))
		for _, exp := range result.Exposures {
			fmt.Printf("  • %s (%s)\n", exp.Description, exp.Type)
		}
	}

	return nil
}

var intelGoogleDorkCmd = &cobra.Command{
	Use:   "dork",
	Short: "Execute Google dork queries",
	Long:  `Execute pre-defined or custom Google dork queries for reconnaissance.`,
	Example: `  # Run specific dork
  vcli intops google dork --query "intitle:index.of config.php"`,
	RunE: runIntelGoogleDork,
}

func runIntelGoogleDork(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.GoogleDorkRequest{
		Dork: intelQuery,
	}

	result, err := client.GoogleDork(req)
	if err != nil {
		return fmt.Errorf("failed to execute dork: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎯 Google Dork Execution Complete"))
	fmt.Printf("\nDork: %s\n", result.Dork)
	fmt.Printf("Findings: %d\n", len(result.Findings))

	if len(result.Findings) > 0 {
		for _, finding := range result.Findings {
			fmt.Printf("\n• %s\n", finding.URL)
			fmt.Printf("  Risk: %s\n", getThreatLevelColor(finding.RiskLevel, styles))
			fmt.Printf("  Description: %s\n", finding.Description)
		}
	}

	return nil
}

// ============================================================================
// IP INTELLIGENCE
// ============================================================================

var intelIPCmd = &cobra.Command{
	Use:   "ip",
	Short: "IP intelligence operations",
	Long:  `Perform IP intelligence, geolocation, and reputation lookups.`,
}

var intelIPLookupCmd = &cobra.Command{
	Use:   "lookup",
	Short: "Lookup IP intelligence",
	Long: `Get comprehensive intelligence about an IP address including geolocation,
ISP information, threat reputation, and historical data.`,
	Example: `  # Lookup IP address
  vcli intops ip lookup --ip 8.8.8.8

  # Lookup with format
  vcli intops ip lookup --ip 1.1.1.1 --format json`,
	RunE: runIntelIPLookup,
}

func runIntelIPLookup(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.IPLookupRequest{
		IP:     intelIP,
		Format: intelFormat,
	}

	result, err := client.LookupIP(req)
	if err != nil {
		return fmt.Errorf("failed to lookup IP: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🌐 IP Intelligence Lookup"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nIP Address:\t%s\n", result.IP)
	fmt.Fprintf(w, "Country:\t%s (%s)\n", result.Country, result.CountryCode)
	fmt.Fprintf(w, "City:\t%s\n", result.City)
	fmt.Fprintf(w, "ISP:\t%s\n", result.ISP)
	fmt.Fprintf(w, "ASN:\t%s\n", result.ASN)
	fmt.Fprintf(w, "Reputation:\t%s\n", getThreatLevelColor(result.Reputation, styles))
	fmt.Fprintf(w, "Threat Score:\t%d/100\n", result.ThreatScore)
	w.Flush()

	if len(result.ThreatIndicators) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Threat Indicators"))
		for _, indicator := range result.ThreatIndicators {
			fmt.Printf("  %s %s\n", getStatusIcon("warning"), indicator)
		}
	}

	return nil
}

var intelIPGeoCmd = &cobra.Command{
	Use:   "geo",
	Short: "Get IP geolocation",
	Long:  `Get detailed geolocation information for an IP address.`,
	Example: `  vcli intops ip geo --ip 8.8.8.8`,
	RunE: runIntelIPGeo,
}

func runIntelIPGeo(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.IPGeoRequest{IP: intelIP}

	result, err := client.GeolocationIP(req)
	if err != nil {
		return fmt.Errorf("failed to get geolocation: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📍 IP Geolocation"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nIP:\t%s\n", result.IP)
	fmt.Fprintf(w, "Latitude:\t%.6f\n", result.Latitude)
	fmt.Fprintf(w, "Longitude:\t%.6f\n", result.Longitude)
	fmt.Fprintf(w, "Country:\t%s\n", result.Country)
	fmt.Fprintf(w, "Region:\t%s\n", result.Region)
	fmt.Fprintf(w, "City:\t%s\n", result.City)
	fmt.Fprintf(w, "Timezone:\t%s\n", result.Timezone)
	w.Flush()

	return nil
}

// ============================================================================
// SINESP (Brazil Government Database)
// ============================================================================

var intelSinespCmd = &cobra.Command{
	Use:   "sinesp",
	Short: "SINESP Brazil government database",
	Long:  `Query SINESP (Sistema Nacional de Informações de Segurança Pública) - Brazil.`,
}

var intelSinespPlateCmd = &cobra.Command{
	Use:   "plate",
	Short: "Lookup vehicle plate",
	Long: `Lookup vehicle information by license plate in SINESP database.

Note: This queries Brazilian government systems and requires appropriate authorization.`,
	Example: `  # Lookup plate
  vcli intops sinesp plate --plate ABC1234`,
	RunE: runIntelSinespPlate,
}

func runIntelSinespPlate(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.SinespPlateRequest{Plate: intelPlate}

	fmt.Println(visual.DefaultStyles().Info.Render("🚗 Querying SINESP database..."))

	result, err := client.SinespPlate(req)
	if err != nil {
		return fmt.Errorf("failed to lookup plate: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ SINESP Plate Lookup"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nPlate:\t%s\n", result.Plate)
	fmt.Fprintf(w, "State:\t%s\n", result.State)
	fmt.Fprintf(w, "City:\t%s\n", result.City)
	fmt.Fprintf(w, "Make:\t%s\n", result.Make)
	fmt.Fprintf(w, "Model:\t%s\n", result.Model)
	fmt.Fprintf(w, "Year:\t%d\n", result.Year)
	fmt.Fprintf(w, "Color:\t%s\n", result.Color)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	w.Flush()

	if len(result.Alerts) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("⚠️  Alerts"))
		for _, alert := range result.Alerts {
			fmt.Printf("  • %s\n", alert)
		}
	}

	return nil
}

var intelSinespDocumentCmd = &cobra.Command{
	Use:   "document",
	Short: "Lookup person by document",
	Long: `Lookup person information by CPF or RG document in SINESP database.

Note: This queries Brazilian government systems and requires appropriate authorization.`,
	Example: `  # Lookup document
  vcli intops sinesp document --document 12345678900`,
	RunE: runIntelSinespDocument,
}

func runIntelSinespDocument(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.SinespDocumentRequest{Document: intelDocument}

	result, err := client.SinespDocument(req)
	if err != nil {
		return fmt.Errorf("failed to lookup document: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ SINESP Document Lookup"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nDocument:\t%s\n", result.Document)
	fmt.Fprintf(w, "Name:\t%s\n", result.Name)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	w.Flush()

	if len(result.Alerts) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("⚠️  Alerts"))
		for _, alert := range result.Alerts {
			fmt.Printf("  • %s\n", alert)
		}
	}

	return nil
}

// ============================================================================
// SSL MONITORING
// ============================================================================

var intelSSLCmd = &cobra.Command{
	Use:   "ssl",
	Short: "SSL/TLS certificate monitoring",
	Long:  `Monitor and analyze SSL/TLS certificates for domains.`,
}

var intelSSLCheckCmd = &cobra.Command{
	Use:   "check",
	Short: "Check SSL certificate",
	Long: `Check SSL/TLS certificate for a domain, including validity, issuer,
and potential security issues.`,
	Example: `  # Check SSL certificate
  vcli intops ssl check --domain example.com

  # Check with detailed output
  vcli intops ssl check --domain secure.example.com --format detailed`,
	RunE: runIntelSSLCheck,
}

func runIntelSSLCheck(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.SSLCheckRequest{
		Domain: intelDomain,
		Format: intelFormat,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔒 Checking SSL certificate..."))

	result, err := client.CheckSSL(req)
	if err != nil {
		return fmt.Errorf("failed to check SSL: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ SSL Certificate Check"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nDomain:\t%s\n", result.Domain)
	fmt.Fprintf(w, "Valid:\t%s\n", getStatusIcon(result.Status))
	fmt.Fprintf(w, "Issuer:\t%s\n", result.Issuer)
	fmt.Fprintf(w, "Valid From:\t%s\n", result.ValidFrom.Format("2006-01-02"))
	fmt.Fprintf(w, "Valid Until:\t%s\n", result.ValidUntil.Format("2006-01-02"))
	fmt.Fprintf(w, "Days Until Expiry:\t%d\n", result.DaysUntilExpiry)
	fmt.Fprintf(w, "Protocol:\t%s\n", result.Protocol)
	fmt.Fprintf(w, "Cipher:\t%s\n", result.Cipher)
	w.Flush()

	if len(result.Warnings) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Warnings"))
		for _, warning := range result.Warnings {
			fmt.Printf("  %s %s\n", getStatusIcon("warning"), warning)
		}
	}

	if len(result.Vulnerabilities) > 0 {
		fmt.Printf("\n%s:\n", styles.Error.Render("Vulnerabilities"))
		for _, vuln := range result.Vulnerabilities {
			fmt.Printf("  %s %s\n", getStatusIcon("error"), vuln)
		}
	}

	return nil
}

var intelSSLMonitorCmd = &cobra.Command{
	Use:   "monitor",
	Short: "Monitor SSL certificates",
	Long:  `Start monitoring SSL certificates for expiry and security issues.`,
	Example: `  # Monitor domain
  vcli intops ssl monitor --domain example.com`,
	RunE: runIntelSSLMonitor,
}

func runIntelSSLMonitor(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.SSLMonitorRequest{Domain: intelDomain}

	result, err := client.MonitorSSL(req)
	if err != nil {
		return fmt.Errorf("failed to start monitoring: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ SSL Monitoring Started"))
	fmt.Printf("\nDomain: %s\n", result.Domain)
	fmt.Printf("Monitoring ID: %s\n", result.MonitorID)
	fmt.Printf("Check Interval: %s\n", result.CheckInterval)
	fmt.Printf("Status: %s\n", getStatusIcon(result.Status))

	return nil
}

// ============================================================================
// NARRATIVE ANALYSIS
// ============================================================================

var intelNarrativeCmd = &cobra.Command{
	Use:   "narrative",
	Short: "Narrative analysis and manipulation detection",
	Long:  `Analyze narratives and detect manipulation, misinformation, and coordinated campaigns.`,
}

var intelNarrativeAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze narrative",
	Long: `Analyze text for narrative patterns, manipulation techniques, and coordinated messaging.

This uses NLP and ML models to identify misinformation, propaganda techniques,
and coordinated influence operations.`,
	Example: `  # Analyze text
  vcli intops narrative analyze --text "suspicious narrative text"

  # Analyze from file
  vcli intops narrative analyze --text "$(cat narrative.txt)"`,
	RunE: runIntelNarrativeAnalyze,
}

func runIntelNarrativeAnalyze(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.NarrativeAnalyzeRequest{Text: intelText}

	fmt.Println(visual.DefaultStyles().Info.Render("📰 Analyzing narrative..."))

	result, err := client.AnalyzeNarrative(req)
	if err != nil {
		return fmt.Errorf("failed to analyze narrative: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Narrative Analysis Complete"))
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nManipulation Score:\t%.2f/10\n", result.ManipulationScore)
	fmt.Fprintf(w, "Credibility Score:\t%.2f/10\n", result.CredibilityScore)
	fmt.Fprintf(w, "Sentiment:\t%s\n", result.Sentiment)
	fmt.Fprintf(w, "Language:\t%s\n", result.Language)
	w.Flush()

	if len(result.Techniques) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Detected Manipulation Techniques"))
		for _, technique := range result.Techniques {
			fmt.Printf("  • %s (confidence: %.2f)\n", technique.Name, technique.Confidence)
			fmt.Printf("    %s\n", technique.Description)
		}
	}

	if len(result.Claims) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Key Claims"))
		for _, claim := range result.Claims {
			fmt.Printf("  • %s\n", claim.Text)
			fmt.Printf("    Veracity: %s (%.2f)\n", claim.Veracity, claim.Confidence)
		}
	}

	return nil
}

var intelNarrativeDetectCmd = &cobra.Command{
	Use:   "detect",
	Short: "Detect narrative manipulation",
	Long: `Detect manipulation, misinformation, and coordinated influence operations.

Focuses specifically on identifying manipulation patterns and coordinated campaigns.`,
	Example: `  vcli intops narrative detect --text "coordinated messaging text"`,
	RunE: runIntelNarrativeDetect,
}

func runIntelNarrativeDetect(cmd *cobra.Command, args []string) error {
	client := intel.NewIntelClient(getIntelServer())

	req := &intel.NarrativeDetectRequest{Text: intelText}

	result, err := client.DetectNarrative(req)
	if err != nil {
		return fmt.Errorf("failed to detect manipulation: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎭 Manipulation Detection"))
	
	fmt.Printf("\nManipulation Detected: %s\n", getStatusIcon(result.Status))
	fmt.Printf("Confidence: %.2f\n", result.Confidence)
	fmt.Printf("Risk Level: %s\n", getThreatLevelColor(result.RiskLevel, styles))

	if len(result.Indicators) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Manipulation Indicators"))
		for _, indicator := range result.Indicators {
			fmt.Printf("  %s %s\n", getStatusIcon("warning"), indicator)
		}
	}

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getIntelServer() string {
	if intelServer != "" {
		return intelServer
	}

	return config.GetEndpoint("intops")
}
