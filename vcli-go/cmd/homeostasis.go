package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/homeostasis"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	homeostasisServer    string
	homeostasisParameter string
	homeostasisValue     string
)

var homeostasisCmd = &cobra.Command{
	Use:   "homeostasis",
	Short: "Homeostatic Regulation - Self-balancing systems",
	Long:  `Manage homeostatic regulation for self-balancing platform health`,
}

var homeostasisStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Homeostasis status",
	RunE:  runHomeostasisStatus,
}

func runHomeostasisStatus(cmd *cobra.Command, args []string) error {
	client := homeostasis.NewHomeostasisClient(getHomeostasisServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Homeostatic Status\n\n", styles.Accent.Render("⚖️"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Balance:"), result.Balance)

	if len(result.Parameters) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Parameters:"))
		for _, param := range result.Parameters {
			fmt.Printf("  %s %s: %.2f\n", getStatusIcon(param.Status), param.Name, param.Value)
		}
	}

	return nil
}

var homeostasisAdjustCmd = &cobra.Command{
	Use:   "adjust",
	Short: "Adjust homeostatic parameter",
	RunE:  runHomeostasisAdjust,
}

func runHomeostasisAdjust(cmd *cobra.Command, args []string) error {
	client := homeostasis.NewHomeostasisClient(getHomeostasisServer())
	req := &homeostasis.AdjustRequest{
		Parameter: homeostasisParameter,
		Value:     homeostasisValue,
	}

	result, err := client.Adjust(req)
	if err != nil {
		return fmt.Errorf("adjustment failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Parameter Adjusted\n\n", styles.Accent.Render("⚙️"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Parameter:"), result.Parameter)
	fmt.Printf("%s %s\n", styles.Muted.Render("Value:"), result.Value)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	return nil
}

func getHomeostasisServer() string {
	if homeostasisServer != "" {
		return homeostasisServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(homeostasisCmd)
	homeostasisCmd.AddCommand(homeostasisStatusCmd)
	homeostasisCmd.AddCommand(homeostasisAdjustCmd)

	homeostasisCmd.PersistentFlags().StringVarP(&homeostasisServer, "server", "s", "", "Homeostasis server endpoint")
	homeostasisAdjustCmd.Flags().StringVar(&homeostasisParameter, "parameter", "", "Parameter to adjust")
	homeostasisAdjustCmd.Flags().StringVar(&homeostasisValue, "value", "", "New value")
}
