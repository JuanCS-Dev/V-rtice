package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/immunity"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for immunity commands
var (
	immunityServer   string
	immunityTarget   string
	immunityPolicy   string
	immunityVaccine  string
	immunityThreat   string
	immunitySeverity string
	immunityMode     string
	immunityZone     string
)

// immunityCmd represents the adaptive immunity command
var immunityCmd = &cobra.Command{
	Use:   "immunity",
	Short: "Adaptive immunity and threat response",
	Long: `Manage the adaptive immunity system for threat detection, response, and prevention.

The immunity system provides bio-inspired adaptive defense mechanisms including
immune core coordination, immunis scanning, vaccine deployment, and antibody response.

Components:
  core         - Immune system core coordination
  scan         - Immunis security scanner
  vaccine      - Vaccine and patch management
  antibody     - Antibody threat response

Examples:
  # Check immune system status
  vcli immunity core status

  # Run security scan
  vcli immunity scan --target system

  # Deploy vaccine
  vcli immunity vaccine deploy --vaccine CVE-2024-1234

  # Generate antibody response
  vcli immunity antibody generate --threat malware-x
`,
}

// ============================================================================
// IMMUNE CORE
// ============================================================================

var immunityCoreCmd = &cobra.Command{
	Use:   "core",
	Short: "Immune system core operations",
	Long:  `Manage core immune system coordination and orchestration.`,
}

var immunityCoreStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get immune system status",
	Long: `Get comprehensive status of the immune system including all subsystems,
active threats, deployed vaccines, and antibody responses.`,
	Example: `  # Get immune system status
  vcli immunity core status

  # Get status for specific zone
  vcli immunity core status --zone production`,
	RunE: runImmunityCoreStatus,
}

func runImmunityCoreStatus(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get immune status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🛡️  Immune System Status"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nZone:\t%s\n", result.Zone)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	fmt.Fprintf(w, "Health:\t%.1f%%\n", result.Health)
	fmt.Fprintf(w, "Active Threats:\t%d\n", result.ActiveThreats)
	fmt.Fprintf(w, "Deployed Vaccines:\t%d\n", result.DeployedVaccines)
	fmt.Fprintf(w, "Active Antibodies:\t%d\n", result.ActiveAntibodies)
	w.Flush()

	if len(result.Subsystems) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Subsystems"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "NAME\tSTATUS\tHEALTH\n")
		fmt.Fprintf(w, "----\t------\t------\n")
		for _, subsys := range result.Subsystems {
			fmt.Fprintf(w, "%s\t%s\t%.1f%%\n",
				subsys.Name,
				getStatusIcon(subsys.Status),
				subsys.Health,
			)
		}
		w.Flush()
	}

	return nil
}

var immunityCoreActivateCmd = &cobra.Command{
	Use:   "activate",
	Short: "Activate immune response",
	Long: `Activate immune system response to detected threats.

This triggers coordinated response across all immunity subsystems.`,
	Example: `  # Activate immune response
  vcli immunity core activate --policy aggressive

  # Activate for specific zone
  vcli immunity core activate --zone dmz --policy containment`,
	RunE: runImmunityCoreActivate,
}

func runImmunityCoreActivate(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	req := &immunity.CoreActivateRequest{
		Zone:   immunityZone,
		Policy: immunityPolicy,
	}

	result, err := client.ActivateResponse(req)
	if err != nil {
		return fmt.Errorf("failed to activate immune response: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Immune Response Activated"))
	fmt.Printf("\nActivation ID: %s\n", result.ActivationID)
	fmt.Printf("Zone: %s\n", result.Zone)
	fmt.Printf("Policy: %s\n", result.Policy)
	fmt.Printf("Status: %s\n", getStatusIcon(result.Status))

	if len(result.ActivatedSubsystems) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Activated Subsystems"))
		for _, subsys := range result.ActivatedSubsystems {
			fmt.Printf("  • %s\n", subsys)
		}
	}

	return nil
}

// ============================================================================
// IMMUNIS SCANNER
// ============================================================================

var immunityScanCmd = &cobra.Command{
	Use:   "scan",
	Short: "Immunis security scanner",
	Long:  `Run Immunis security scans to detect vulnerabilities and threats.`,
	Example: `  # Scan system
  vcli immunity scan --target system

  # Deep scan with specific mode
  vcli immunity scan --target network --mode deep`,
	RunE: runImmunityScan,
}

func runImmunityScan(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	req := &immunity.ImmunisScanRequest{
		Target: immunityTarget,
		Mode:   immunityMode,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔬 Running Immunis scan..."))

	result, err := client.Scan(req)
	if err != nil {
		return fmt.Errorf("failed to run scan: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Immunis Scan Complete"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTarget:\t%s\n", result.Target)
	fmt.Fprintf(w, "Scan ID:\t%s\n", result.ScanID)
	fmt.Fprintf(w, "Duration:\t%.2fs\n", result.Duration)
	fmt.Fprintf(w, "Items Scanned:\t%d\n", result.ItemsScanned)
	fmt.Fprintf(w, "Vulnerabilities:\t%d\n", len(result.Vulnerabilities))
	w.Flush()

	if len(result.Vulnerabilities) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Vulnerabilities Found"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "CVE\tSEVERITY\tCOMPONENT\tSTATUS\n")
		fmt.Fprintf(w, "---\t--------\t---------\t------\n")
		for _, vuln := range result.Vulnerabilities {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
				vuln.CVE,
				getSeverityEmoji(vuln.SeverityScore),
				vuln.Component,
				vuln.Status,
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// VACCINE MANAGEMENT
// ============================================================================

var immunityVaccineCmd = &cobra.Command{
	Use:   "vaccine",
	Short: "Vaccine and patch management",
	Long:  `Manage vaccines (patches, updates) for known vulnerabilities.`,
}

var immunityVaccineDeployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy vaccine",
	Long: `Deploy a vaccine to protect against a specific vulnerability.

Vaccines can be patches, configuration changes, or behavioral rules.`,
	Example: `  # Deploy vaccine for CVE
  vcli immunity vaccine deploy --vaccine CVE-2024-1234

  # Deploy to specific zone
  vcli immunity vaccine deploy --vaccine CVE-2024-5678 --zone production`,
	RunE: runImmunityVaccineDeploy,
}

func runImmunityVaccineDeploy(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	req := &immunity.VaccineDeployRequest{
		Vaccine: immunityVaccine,
		Zone:    immunityZone,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("💉 Deploying vaccine..."))

	result, err := client.DeployVaccine(req)
	if err != nil {
		return fmt.Errorf("failed to deploy vaccine: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Vaccine Deployed"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nVaccine:\t%s\n", result.Vaccine)
	fmt.Fprintf(w, "Deployment ID:\t%s\n", result.DeploymentID)
	fmt.Fprintf(w, "Zone:\t%s\n", result.Zone)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	fmt.Fprintf(w, "Hosts Protected:\t%d\n", result.HostsProtected)
	w.Flush()

	if len(result.ProtectedComponents) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Protected Components"))
		for _, comp := range result.ProtectedComponents {
			fmt.Printf("  ✓ %s\n", comp)
		}
	}

	return nil
}

var immunityVaccineListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available vaccines",
	Long:  `List available vaccines for deployment.`,
	Example: `  # List all vaccines
  vcli immunity vaccine list

  # List vaccines for zone
  vcli immunity vaccine list --zone production`,
	RunE: runImmunityVaccineList,
}

func runImmunityVaccineList(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	result, err := client.ListVaccines()
	if err != nil {
		return fmt.Errorf("failed to list vaccines: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("💉 Available Vaccines"))

	if len(result.Vaccines) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nVACCINE\tTYPE\tSEVERITY\tDEPLOYED\n")
		fmt.Fprintf(w, "-------\t----\t--------\t--------\n")
		for _, vac := range result.Vaccines {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
				vac.Name,
				vac.Type,
				vac.Severity,
				getStatusIcon(vac.DeploymentStatus),
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// ANTIBODY RESPONSE
// ============================================================================

var immunityAntibodyCmd = &cobra.Command{
	Use:   "antibody",
	Short: "Antibody threat response",
	Long:  `Generate and deploy antibodies for active threat response.`,
}

var immunityAntibodyGenerateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Generate antibody response",
	Long: `Generate antibody response to neutralize an active threat.

Antibodies are dynamic countermeasures tailored to specific threats.`,
	Example: `  # Generate antibody for threat
  vcli immunity antibody generate --threat malware-x

  # Generate with severity
  vcli immunity antibody generate --threat apt-campaign --severity critical`,
	RunE: runImmunityAntibodyGenerate,
}

func runImmunityAntibodyGenerate(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	req := &immunity.AntibodyGenerateRequest{
		Threat:   immunityThreat,
		Severity: immunitySeverity,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🦠 Generating antibody response..."))

	result, err := client.GenerateAntibody(req)
	if err != nil {
		return fmt.Errorf("failed to generate antibody: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Antibody Generated"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nAntibody ID:\t%s\n", result.AntibodyID)
	fmt.Fprintf(w, "Threat:\t%s\n", result.Threat)
	fmt.Fprintf(w, "Type:\t%s\n", result.Type)
	fmt.Fprintf(w, "Efficacy:\t%.1f%%\n", result.Efficacy)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	w.Flush()

	if len(result.Countermeasures) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Countermeasures"))
		for _, cm := range result.Countermeasures {
			fmt.Printf("  • %s: %s\n", cm.Type, cm.Description)
		}
	}

	return nil
}

var immunityAntibodyListCmd = &cobra.Command{
	Use:   "list",
	Short: "List active antibodies",
	Long:  `List all active antibody responses.`,
	Example: `  # List all antibodies
  vcli immunity antibody list

  # List for zone
  vcli immunity antibody list --zone production`,
	RunE: runImmunityAntibodyList,
}

func runImmunityAntibodyList(cmd *cobra.Command, args []string) error {
	client := immunity.NewImmunityClient(getImmunityServer())

	result, err := client.ListAntibodies()
	if err != nil {
		return fmt.Errorf("failed to list antibodies: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🦠 Active Antibodies"))

	if len(result.Antibodies) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nID\tTHREAT\tTYPE\tEFFICACY\tSTATUS\n")
		fmt.Fprintf(w, "--\t------\t----\t--------\t------\n")
		for _, ab := range result.Antibodies {
			fmt.Fprintf(w, "%s\t%s\t%s\t%.1f%%\t%s\n",
				ab.ID,
				ab.Threat,
				ab.Type,
				ab.Efficacy,
				getStatusIcon(ab.Status),
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getImmunityServer() string {
	if immunityServer != "" {
		return immunityServer
	}

	return config.GetEndpoint("immunity")
}
