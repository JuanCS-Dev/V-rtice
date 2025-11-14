package cmd

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/offensive"
	"github.com/verticedev/vcli-go/internal/threat"
)

var threatCmd = &cobra.Command{
	Use:   "threat",
	Short: "Threat intelligence and offensive security",
	Long:  "Threat services: intel (threat intelligence), vuln (vulnerability intel), attack (web attacks)",
}

var intelCmd = &cobra.Command{Use: "intel", Short: "Threat Intelligence operations"}
var vulnCmd = &cobra.Command{Use: "vuln", Short: "Vulnerability Intelligence operations"}
var attackCmd = &cobra.Command{Use: "attack", Short: "Web Attack operations"}

var intelQueryCmd = &cobra.Command{Use: "query", Short: "Query threat intel", RunE: runIntelQuery}
var intelStatusCmd = &cobra.Command{Use: "status", Short: "Get intel status", RunE: runIntelStatus}
var intelHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runIntelHealth}

var vulnQueryCmd = &cobra.Command{Use: "query", Short: "Query vulnerability", RunE: runVulnQuery}
var vulnHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runVulnHealth}

var attackLaunchCmd = &cobra.Command{Use: "launch", Short: "Launch web attack", RunE: runAttackLaunch}
var attackStatusCmd = &cobra.Command{Use: "status <attack_id>", Short: "Get attack status", Args: cobra.ExactArgs(1), RunE: runAttackStatus}
var attackHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runAttackHealth}

var (
	intelEndpoint  string
	vulnEndpoint   string
	attackEndpoint string
	threatToken    string

	indicator      string
	indicatorType  string
	cveID          string
	product        string
	productVersion string
	targetURL      string
	attackType     string
	paramsFile     string
)

func init() {
	rootCmd.AddCommand(threatCmd)
	threatCmd.AddCommand(intelCmd, vulnCmd, attackCmd)

	intelCmd.AddCommand(intelQueryCmd, intelStatusCmd, intelHealthCmd)
	vulnCmd.AddCommand(vulnQueryCmd, vulnHealthCmd)
	attackCmd.AddCommand(attackLaunchCmd, attackStatusCmd, attackHealthCmd)

	intelCmd.PersistentFlags().StringVar(&intelEndpoint, "intel-endpoint", "http://localhost:8037", "Threat Intel endpoint")
	vulnCmd.PersistentFlags().StringVar(&vulnEndpoint, "vuln-endpoint", "http://localhost:8038", "Vuln Intel endpoint")
	attackCmd.PersistentFlags().StringVar(&attackEndpoint, "attack-endpoint", "http://localhost:8039", "Web Attack endpoint")

	threatCmd.PersistentFlags().StringVar(&threatToken, "token", "", "Authentication token")

	intelQueryCmd.Flags().StringVar(&indicator, "indicator", "", "Indicator (IP, domain, hash)")
	intelQueryCmd.Flags().StringVar(&indicatorType, "type", "ip", "Indicator type")
	intelQueryCmd.MarkFlagRequired("indicator")

	vulnQueryCmd.Flags().StringVar(&cveID, "cve", "", "CVE ID")
	vulnQueryCmd.Flags().StringVar(&product, "product", "", "Product name")
	vulnQueryCmd.Flags().StringVar(&productVersion, "product-version", "", "Product version")

	attackLaunchCmd.Flags().StringVar(&targetURL, "target", "", "Target URL")
	attackLaunchCmd.Flags().StringVar(&attackType, "attack-type", "scan", "Attack type (scan, sqli, xss)")
	attackLaunchCmd.Flags().StringVar(&paramsFile, "params-file", "", "Parameters file (JSON)")
	attackLaunchCmd.MarkFlagRequired("target")
}

func runIntelQuery(cmd *cobra.Command, args []string) error {
	client := threat.NewIntelClient(intelEndpoint, threatToken)
	result, err := client.QueryThreatIntel(indicator, indicatorType, nil)
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIntelStatus(cmd *cobra.Command, args []string) error {
	client := threat.NewIntelClient(intelEndpoint, threatToken)
	result, _ := client.GetStatus()
	printJSON(result)
	return nil
}

func runIntelHealth(cmd *cobra.Command, args []string) error {
	client := threat.NewIntelClient(intelEndpoint, threatToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

func runVulnQuery(cmd *cobra.Command, args []string) error {
	client := threat.NewVulnClient(vulnEndpoint, threatToken)
	result, err := client.QueryVulnerability(cveID, product, productVersion, nil)
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runVulnHealth(cmd *cobra.Command, args []string) error {
	client := threat.NewVulnClient(vulnEndpoint, threatToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

func runAttackLaunch(cmd *cobra.Command, args []string) error {
	client := offensive.NewWebAttackClient(attackEndpoint, threatToken)

	var params map[string]interface{}
	if paramsFile != "" {
		paramsRaw, err := readJSONFile(paramsFile)
		if err != nil {
			return err
		}
		if paramsRaw != nil {
			params = paramsRaw.(map[string]interface{})
		}
	}

	result, err := client.LaunchAttack(targetURL, attackType, params)
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runAttackStatus(cmd *cobra.Command, args []string) error {
	client := offensive.NewWebAttackClient(attackEndpoint, threatToken)
	result, _ := client.GetAttackStatus(args[0])
	printJSON(result)
	return nil
}

func runAttackHealth(cmd *cobra.Command, args []string) error {
	client := offensive.NewWebAttackClient(attackEndpoint, threatToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}
