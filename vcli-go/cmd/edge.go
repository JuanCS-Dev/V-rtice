package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/edge"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	edgeServer string
	edgeAgent  string
	edgeTarget string
)

var edgeCmd = &cobra.Command{
	Use:   "edge",
	Short: "Edge Agents - Distributed edge deployment",
	Long:  `Deploy and manage edge agents for distributed sensing and response`,
}

var edgeDeployCmd = &cobra.Command{
	Use:   "deploy [agent]",
	Short: "Deploy edge agent",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runEdgeDeploy,
}

func runEdgeDeploy(cmd *cobra.Command, args []string) error {
	client := edge.NewEdgeClient(getEdgeServer())
	req := &edge.DeployRequest{Agent: args[0], Target: edgeTarget}

	result, err := client.Deploy(req)
	if err != nil {
		return fmt.Errorf("deployment failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Edge Agent Deployed\n\n", styles.Accent.Render("🌍"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Agent:"), result.Agent)
	fmt.Printf("%s %s\n", styles.Muted.Render("Target:"), result.Target)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	return nil
}

var edgeListCmd = &cobra.Command{
	Use:   "list",
	Short: "List edge agents",
	RunE:  runEdgeList,
}

func runEdgeList(cmd *cobra.Command, args []string) error {
	client := edge.NewEdgeClient(getEdgeServer())
	result, err := client.List()
	if err != nil {
		return fmt.Errorf("failed to list agents: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Edge Agents\n\n", styles.Accent.Render("🌍"))

	for _, agent := range result.Agents {
		fmt.Printf("%s %s\n", getStatusIcon(agent.Status), agent.Name)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Target:"), agent.Target)
		fmt.Printf("  %s %s\n\n", styles.Muted.Render("Version:"), agent.Version)
	}

	return nil
}

var edgeStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Edge service status",
	RunE:  runEdgeStatus,
}

func runEdgeStatus(cmd *cobra.Command, args []string) error {
	client := edge.NewEdgeClient(getEdgeServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Edge Service Status\n\n", styles.Accent.Render("🌐"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d agents\n", styles.Muted.Render("Active:"), result.ActiveAgents)

	return nil
}

func getEdgeServer() string {
	if edgeServer != "" {
		return edgeServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(edgeCmd)
	edgeCmd.AddCommand(edgeDeployCmd)
	edgeCmd.AddCommand(edgeListCmd)
	edgeCmd.AddCommand(edgeStatusCmd)

	edgeCmd.PersistentFlags().StringVarP(&edgeServer, "server", "s", "", "Edge server endpoint")
	edgeDeployCmd.Flags().StringVar(&edgeTarget, "target", "", "Deployment target")
}
