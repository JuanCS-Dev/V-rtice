package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/grpc"
	pb "github.com/verticedev/vcli-go/api/grpc/immune"
)

// Flags
var (
	immuneServer string

	// Agent flags
	agentID        string
	lymphnodeID    string
	agentTypeStr   string
	agentStateStr  string
	cloneCount     int32
	includeMetrics bool
	includeHistory bool
	terminateGraceful bool
	terminateReason string

	// Cytokine flags
	cytokineTopics   []string
	cytokineEventType string
	cytokineSeverityMin int32

	// Hormone flags
	hormoneTypes []string

	// Mass response flags
	threatType string
	massAgentCount int32
	massReason string

	// Common flags
	zone string
)

// ============================================================
// ROOT COMMAND
// ============================================================

var immuneCmd = &cobra.Command{
	Use:   "immune",
	Short: "Interact with Active Immune Core",
	Long: `Manage the bio-inspired digital immune system.

Active Immune Core orchestrates autonomous agents (Neutrophils, Macrophages,
Dendritic Cells, etc.) that detect and respond to cyber threats in real-time.

Agent Types:
  neutrophil    - Fast response, short-lived threat hunters
  macrophage    - Phagocytosis and antigen presentation
  dendritic     - Immune system activation and coordination
  t-cell        - Adaptive immunity coordination
  memory-cell   - Long-term immunity memory

Examples:
  # List all active agents
  vcli immune agents list --state ACTIVE

  # Clone a high-performing agent
  vcli immune agents clone agent_abc123 --count 10

  # Stream threat cytokines in real-time
  vcli immune cytokines stream --event-type ameaca_detectada --severity 7

  # Check system health
  vcli immune health --all`,
}

// ============================================================
// AGENTS COMMANDS
// ============================================================

var immuneAgentsCmd = &cobra.Command{
	Use:   "agents",
	Short: "Manage immune agents",
	Long: `Manage autonomous immune agents.

Agents are the core operational units of the immune system. Each agent type
has specialized capabilities for detecting and responding to threats.`,
}

var immuneAgentsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List immune agents",
	Long: `List agents with optional filters.

Filter by lymphnode, agent type, state, and more.

Agent States:
  INACTIVE  - Agent initialized but not active
  ACTIVE    - Agent actively patrolling
  HUNTING   - Agent pursuing a threat
  ATTACKING - Agent neutralizing a threat
  RESTING   - Agent recovering energy
  DYING     - Agent approaching end of life
  MEMORY    - Long-term memory agent

Examples:
  # List all active agents
  vcli immune agents list --state ACTIVE

  # List neutrophils in specific lymphnode
  vcli immune agents list \
    --lymphnode ln-us-east-1 \
    --type neutrophil

  # List hunting agents with metrics
  vcli immune agents list \
    --state HUNTING \
    --metrics`,
	RunE: runListAgents,
}

func runListAgents(cmd *cobra.Command, args []string) error {
	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Parse agent type
	agentType := pb.AgentType_AGENT_TYPE_UNSPECIFIED
	if agentTypeStr != "" {
		agentType = parseAgentType(agentTypeStr)
	}

	// Parse agent state
	state := pb.AgentState_STATE_UNSPECIFIED
	if agentStateStr != "" {
		state = parseAgentState(agentStateStr)
	}

	resp, err := client.ListAgents(ctx, lymphnodeID, agentType, state, page, pageSize, includeMetrics)
	if err != nil {
		return fmt.Errorf("failed to list agents: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	if len(resp.Agents) == 0 {
		fmt.Println("No agents found")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "ID\tTYPE\tSTATE\tENERGY\tTHREATS\tAGE\tLYMPHNODE")
	for _, a := range resp.Agents {
		fmt.Fprintf(w, "%s\t%s\t%s\t%.0f%%\t%d/%d\t%ds\t%s\n",
			truncate(a.AgentId, 16),
			agentTypeToString(a.Type),
			stateToString(a.State),
			a.Energia,
			a.ThreatsNeutralized,
			a.ThreatsDetected,
			a.AgeSeconds,
			truncate(a.LymphnodeId, 16),
		)
	}
	w.Flush()

	fmt.Printf("\nShowing %d of %d total agents\n", len(resp.Agents), resp.TotalCount)
	return nil
}

var immuneAgentsGetCmd = &cobra.Command{
	Use:   "get <agent-id>",
	Short: "Get agent details",
	Long: `Get detailed information about a specific agent.

Examples:
  # Get agent details
  vcli immune agents get agent_abc123

  # Get agent with metrics
  vcli immune agents get agent_abc123 --metrics

  # Get agent with full history
  vcli immune agents get agent_abc123 --metrics --history`,
	Args: cobra.ExactArgs(1),
	RunE: runGetAgent,
}

func runGetAgent(cmd *cobra.Command, args []string) error {
	agentID := args[0]

	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	agent, err := client.GetAgent(ctx, agentID, includeMetrics, includeHistory)
	if err != nil {
		return fmt.Errorf("failed to get agent: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(agent, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("Agent: %s\n", agent.AgentId)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Type:        %s\n", agentTypeToString(agent.Type))
	fmt.Printf("State:       %s\n", stateToString(agent.State))
	fmt.Printf("Lymphnode:   %s\n", agent.LymphnodeId)
	fmt.Printf("\n")
	fmt.Printf("Vitals:\n")
	fmt.Printf("  Energy:        %.1f%%\n", agent.Energia)
	fmt.Printf("  Sensitivity:   %.1f/10\n", agent.Sensibilidade)
	fmt.Printf("  Aggressiveness: %.1f/10\n", agent.NivelAgressividade)
	fmt.Printf("  Temperature:   %.1f°\n", agent.Temperatura)
	fmt.Printf("\n")
	fmt.Printf("Activity:\n")
	fmt.Printf("  Threats Detected:    %d\n", agent.ThreatsDetected)
	fmt.Printf("  Threats Neutralized: %d\n", agent.ThreatsNeutralized)
	fmt.Printf("  Cytokines Emitted:   %d\n", agent.CytokinesEmitted)
	fmt.Printf("\n")
	fmt.Printf("Lifecycle:\n")
	fmt.Printf("  Age:           %ds (max: %ds)\n", agent.AgeSeconds, agent.MaxAgeSeconds)
	fmt.Printf("  Created:       %s\n", agent.CreatedAt.AsTime().Format(time.RFC3339))
	fmt.Printf("  Last Heartbeat: %s\n", agent.LastHeartbeat.AsTime().Format(time.RFC3339))

	if agent.CurrentZone != "" {
		fmt.Printf("\n")
		fmt.Printf("Location:\n")
		fmt.Printf("  Zone:         %s\n", agent.CurrentZone)
		fmt.Printf("  Patrol Area:  %s\n", agent.PatrolArea)
	}

	return nil
}

var immuneAgentsCloneCmd = &cobra.Command{
	Use:   "clone <agent-id>",
	Short: "Clone an agent",
	Long: `Clone an agent multiple times for mass response.

Cloning replicates successful agent patterns to scale response to threats.

Examples:
  # Clone agent 10 times
  vcli immune agents clone agent_abc123 --count 10

  # Clone to specific lymphnode
  vcli immune agents clone agent_abc123 \
    --count 5 \
    --lymphnode ln-us-west-1`,
	Args: cobra.ExactArgs(1),
	RunE: runCloneAgent,
}

func runCloneAgent(cmd *cobra.Command, args []string) error {
	agentID := args[0]

	if cloneCount <= 0 {
		return fmt.Errorf("clone count must be > 0")
	}

	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.CloneAgent(ctx, agentID, cloneCount, lymphnodeID)
	if err != nil {
		return fmt.Errorf("failed to clone agent: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	fmt.Printf("✅ Agent cloned successfully\n")
	fmt.Printf("Success: %d/%d clones created\n", resp.SuccessCount, cloneCount)
	if resp.FailureCount > 0 {
		fmt.Printf("⚠️  Failed: %d clones\n", resp.FailureCount)
		for _, err := range resp.Errors {
			fmt.Printf("  - %s\n", err)
		}
	}
	if len(resp.ClonedAgentIds) > 0 && len(resp.ClonedAgentIds) <= 20 {
		fmt.Printf("\nCloned Agent IDs:\n")
		for _, id := range resp.ClonedAgentIds {
			fmt.Printf("  - %s\n", id)
		}
	}

	return nil
}

var immuneAgentsTerminateCmd = &cobra.Command{
	Use:   "terminate <agent-id>",
	Short: "Terminate an agent",
	Long: `Terminate an agent gracefully or forcefully.

Graceful termination allows agent to complete current task.
Force termination immediately stops the agent.

Examples:
  # Graceful termination
  vcli immune agents terminate agent_abc123 \
    --graceful \
    --reason "Task complete"

  # Force termination
  vcli immune agents terminate agent_abc123 \
    --reason "Malfunctioning"`,
	Args: cobra.ExactArgs(1),
	RunE: runTerminateAgent,
}

func runTerminateAgent(cmd *cobra.Command, args []string) error {
	agentID := args[0]

	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	resp, err := client.TerminateAgent(ctx, agentID, terminateReason, terminateGraceful)
	if err != nil {
		return fmt.Errorf("failed to terminate agent: %w", err)
	}

	if resp.Success {
		fmt.Printf("✅ Agent %s terminated\n", agentID)
		if resp.Message != "" {
			fmt.Printf("Message: %s\n", resp.Message)
		}
		fmt.Printf("Terminated at: %s\n", resp.TerminatedAt.AsTime().Format(time.RFC3339))
	} else {
		fmt.Printf("❌ Failed to terminate agent\n")
		fmt.Printf("Message: %s\n", resp.Message)
	}

	return nil
}

// ============================================================
// LYMPHNODES COMMANDS
// ============================================================

var immuneLymphnodesCmd = &cobra.Command{
	Use:   "lymphnodes",
	Short: "Manage lymphnodes",
	Long: `Lymphnode operations.

Lymphnodes are regional coordination hubs that manage agent populations,
aggregate cytokines, detect patterns, and trigger immune responses.`,
}

var immuneLymphnodesListCmd = &cobra.Command{
	Use:   "list",
	Short: "List lymphnodes",
	Long: `List all lymphnodes with status.

Examples:
  # List all lymphnodes
  vcli immune lymphnodes list

  # List lymphnodes in specific zone
  vcli immune lymphnodes list --zone us-east-1

  # List with metrics
  vcli immune lymphnodes list --metrics`,
	RunE: runListLymphnodes,
}

func runListLymphnodes(cmd *cobra.Command, args []string) error {
	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.ListLymphnodes(ctx, zone, includeMetrics)
	if err != nil {
		return fmt.Errorf("failed to list lymphnodes: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	if len(resp.Lymphnodes) == 0 {
		fmt.Println("No lymphnodes found")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "ID\tZONE\tREGION\tSTATUS\tTEMP\tAGENTS\tCYTOKINES/s")
	for _, ln := range resp.Lymphnodes {
		healthIcon := "✅"
		if !ln.IsHealthy {
			healthIcon = "❌"
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s %s\t%.1f°\t%d\t%d\n",
			truncate(ln.LymphnodeId, 16),
			ln.Zone,
			ln.Region,
			healthIcon,
			ln.Status,
			ln.Temperature,
			ln.TotalAgents,
			ln.CytokinesPerSecond,
		)
	}
	w.Flush()

	fmt.Printf("\nTotal lymphnodes: %d\n", resp.TotalCount)
	return nil
}

var immuneLymphnodesStatusCmd = &cobra.Command{
	Use:   "status <lymphnode-id>",
	Short: "Get lymphnode detailed status",
	Long: `Get detailed status of a lymphnode including health checks.

Examples:
  # Get lymphnode status
  vcli immune lymphnodes status ln-us-east-1`,
	Args: cobra.ExactArgs(1),
	RunE: runLymphnodeStatus,
}

func runLymphnodeStatus(cmd *cobra.Command, args []string) error {
	lymphnodeID := args[0]

	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	status, err := client.GetLymphnodeStatus(ctx, lymphnodeID)
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(status, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	ln := status.Lymphnode
	fmt.Printf("Lymphnode: %s\n", ln.LymphnodeId)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Zone:        %s\n", ln.Zone)
	fmt.Printf("Region:      %s\n", ln.Region)
	fmt.Printf("Status:      %s\n", ln.Status)
	fmt.Printf("Healthy:     %v\n", ln.IsHealthy)
	fmt.Printf("Temperature: %.1f°\n", ln.Temperature)
	fmt.Printf("\n")
	fmt.Printf("Agents:\n")
	fmt.Printf("  Total: %d\n", ln.TotalAgents)
	if len(ln.AgentsByType) > 0 {
		fmt.Printf("  By Type:\n")
		for typ, count := range ln.AgentsByType {
			fmt.Printf("    %s: %d\n", typ, count)
		}
	}
	fmt.Printf("\n")
	fmt.Printf("Activity:\n")
	fmt.Printf("  Cytokines/sec:  %d\n", ln.CytokinesPerSecond)
	fmt.Printf("  Active Threats: %d\n", ln.ThreatsActive)
	fmt.Printf("\n")
	fmt.Printf("Resources:\n")
	fmt.Printf("  CPU:        %.1f%%\n", status.CpuPercent)
	fmt.Printf("  Memory:     %.1f MB\n", status.MemoryMb)
	fmt.Printf("  Kafka Lag:  %d\n", status.KafkaLag)

	if len(status.HealthChecks) > 0 {
		fmt.Printf("\n")
		fmt.Printf("Health Checks:\n")
		for _, hc := range status.HealthChecks {
			icon := "✅"
			if !hc.Healthy {
				icon = "❌"
			}
			fmt.Printf("  %s %s: %s\n", icon, hc.Component, hc.Message)
		}
	}

	if len(status.Warnings) > 0 {
		fmt.Printf("\n⚠️  Warnings:\n")
		for _, w := range status.Warnings {
			fmt.Printf("  - %s\n", w)
		}
	}

	if len(status.Errors) > 0 {
		fmt.Printf("\n❌ Errors:\n")
		for _, e := range status.Errors {
			fmt.Printf("  - %s\n", e)
		}
	}

	return nil
}

// ============================================================
// CYTOKINES COMMANDS
// ============================================================

var immuneCytokinesCmd = &cobra.Command{
	Use:   "cytokines",
	Short: "Stream cytokine events",
	Long: `Cytokines are communication molecules emitted by agents.

They carry information about threats, status changes, and coordination signals.`,
}

var immuneCytokinesStreamCmd = &cobra.Command{
	Use:   "stream",
	Short: "Stream cytokines in real-time",
	Long: `Stream cytokine events in real-time via gRPC.

Filter by topics, event types, severity, and lymphnode.

Examples:
  # Stream all cytokines
  vcli immune cytokines stream

  # Stream high-severity threats only
  vcli immune cytokines stream \
    --event-type ameaca_detectada \
    --severity 7

  # Stream from specific lymphnode
  vcli immune cytokines stream --lymphnode ln-us-east-1

  Press Ctrl+C to stop.`,
	RunE: runStreamCytokines,
}

func runStreamCytokines(cmd *cobra.Command, args []string) error {
	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	fmt.Printf("🧬 Streaming cytokines...\n")
	fmt.Printf("Press Ctrl+C to stop\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	ctx := context.Background()

	err = client.StreamCytokines(
		ctx,
		cytokineTopics,
		lymphnodeID,
		cytokineEventType,
		cytokineSeverityMin,
		func(c *pb.Cytokine) error {
			severityIcon := getSeverityIcon(c.Severity)
			fmt.Printf("[%s] %s %s (severity:%d)\n",
				c.Timestamp.AsTime().Format("15:04:05"),
				severityIcon,
				c.EventType,
				c.Severity,
			)
			fmt.Printf("  Emitter:    %s\n", truncate(c.EmitterId, 32))
			fmt.Printf("  Lymphnode:  %s\n", truncate(c.LymphnodeId, 32))
			if c.Zone != "" {
				fmt.Printf("  Zone:       %s\n", c.Zone)
			}
			if len(c.Tags) > 0 {
				fmt.Printf("  Tags:       %s\n", strings.Join(c.Tags, ", "))
			}
			fmt.Println()
			return nil
		},
	)

	if err != nil {
		return fmt.Errorf("stream error: %w", err)
	}

	return nil
}

// ============================================================
// SYSTEM HEALTH
// ============================================================

var immuneHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Get immune system health",
	Long: `Get overall immune system health status.

Includes lymphnode health, agent statistics, and service status.

Examples:
  # Quick health check
  vcli immune health

  # Detailed health with all lymphnodes
  vcli immune health --all`,
	RunE: runSystemHealth,
}

func runSystemHealth(cmd *cobra.Command, args []string) error {
	client, err := grpc.NewImmuneClient(immuneServer)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	includeAll := cmd.Flags().Changed("all")
	resp, err := client.GetSystemHealth(ctx, includeAll, includeAll)
	if err != nil {
		return fmt.Errorf("failed to get health: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	statusIcon := getHealthIcon(resp.Status)
	fmt.Printf("%s Immune System Status: %s\n", statusIcon, resp.Status.String())
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	fmt.Printf("Lymphnodes:\n")
	fmt.Printf("  Total:   %d\n", resp.TotalLymphnodes)
	fmt.Printf("  Healthy: %d\n", resp.HealthyLymphnodes)
	fmt.Printf("\n")
	fmt.Printf("Agents:\n")
	fmt.Printf("  Total:  %d\n", resp.TotalAgents)
	fmt.Printf("  Active: %d\n", resp.ActiveAgents)
	fmt.Printf("\n")
	fmt.Printf("Services:\n")
	for service, healthy := range resp.Services {
		icon := "✅"
		if !healthy {
			icon = "❌"
		}
		fmt.Printf("  %s %s\n", icon, service)
	}

	if includeAll && len(resp.LymphnodeStatuses) > 0 {
		fmt.Printf("\nLymphnode Details:\n")
		for _, ls := range resp.LymphnodeStatuses {
			icon := "✅"
			if !ls.Lymphnode.IsHealthy {
				icon = "❌"
			}
			fmt.Printf("  %s %s (%s) - %d agents, %.1f°\n",
				icon,
				ls.Lymphnode.LymphnodeId,
				ls.Lymphnode.Zone,
				ls.Lymphnode.TotalAgents,
				ls.Lymphnode.Temperature,
			)
		}
	}

	return nil
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

func parseAgentType(s string) pb.AgentType {
	switch strings.ToLower(s) {
	case "neutrophil":
		return pb.AgentType_NEUTROPHIL
	case "macrophage":
		return pb.AgentType_MACROPHAGE
	case "dendritic", "dendritic_cell":
		return pb.AgentType_DENDRITIC_CELL
	case "t-cell", "tcell":
		return pb.AgentType_T_CELL
	case "b-cell", "bcell":
		return pb.AgentType_B_CELL
	case "memory", "memory_cell":
		return pb.AgentType_MEMORY_CELL
	case "nk", "nk_cell":
		return pb.AgentType_NK_CELL
	default:
		return pb.AgentType_AGENT_TYPE_UNSPECIFIED
	}
}

func parseAgentState(s string) pb.AgentState {
	switch strings.ToUpper(s) {
	case "INACTIVE":
		return pb.AgentState_INACTIVE
	case "ACTIVE":
		return pb.AgentState_ACTIVE
	case "HUNTING":
		return pb.AgentState_HUNTING
	case "ATTACKING":
		return pb.AgentState_ATTACKING
	case "RESTING":
		return pb.AgentState_RESTING
	case "DYING":
		return pb.AgentState_DYING
	case "DEAD":
		return pb.AgentState_DEAD
	case "MEMORY":
		return pb.AgentState_MEMORY
	default:
		return pb.AgentState_STATE_UNSPECIFIED
	}
}

func agentTypeToString(t pb.AgentType) string {
	switch t {
	case pb.AgentType_NEUTROPHIL:
		return "Neutrophil"
	case pb.AgentType_MACROPHAGE:
		return "Macrophage"
	case pb.AgentType_DENDRITIC_CELL:
		return "Dendritic"
	case pb.AgentType_T_CELL:
		return "T-Cell"
	case pb.AgentType_B_CELL:
		return "B-Cell"
	case pb.AgentType_MEMORY_CELL:
		return "Memory"
	case pb.AgentType_NK_CELL:
		return "NK-Cell"
	default:
		return "Unknown"
	}
}

func stateToString(s pb.AgentState) string {
	switch s {
	case pb.AgentState_INACTIVE:
		return "Inactive"
	case pb.AgentState_ACTIVE:
		return "Active"
	case pb.AgentState_HUNTING:
		return "Hunting"
	case pb.AgentState_ATTACKING:
		return "Attacking"
	case pb.AgentState_RESTING:
		return "Resting"
	case pb.AgentState_DYING:
		return "Dying"
	case pb.AgentState_DEAD:
		return "Dead"
	case pb.AgentState_MEMORY:
		return "Memory"
	default:
		return "Unknown"
	}
}

func getSeverityIcon(severity int32) string {
	if severity >= 9 {
		return "🔴"
	} else if severity >= 7 {
		return "🟠"
	} else if severity >= 4 {
		return "🟡"
	}
	return "🟢"
}

func getHealthIcon(status pb.SystemHealthResponse_OverallStatus) string {
	switch status {
	case pb.SystemHealthResponse_HEALTHY:
		return "✅"
	case pb.SystemHealthResponse_DEGRADED:
		return "⚠️"
	case pb.SystemHealthResponse_CRITICAL:
		return "🔴"
	default:
		return "❓"
	}
}

// ============================================================
// INIT
// ============================================================

func init() {
	rootCmd.AddCommand(immuneCmd)

	// Add subcommands
	immuneCmd.AddCommand(immuneAgentsCmd)
	immuneCmd.AddCommand(immuneLymphnodesCmd)
	immuneCmd.AddCommand(immuneCytokinesCmd)
	immuneCmd.AddCommand(immuneHealthCmd)

	// Agents subcommands
	immuneAgentsCmd.AddCommand(immuneAgentsListCmd)
	immuneAgentsCmd.AddCommand(immuneAgentsGetCmd)
	immuneAgentsCmd.AddCommand(immuneAgentsCloneCmd)
	immuneAgentsCmd.AddCommand(immuneAgentsTerminateCmd)

	// Lymphnodes subcommands
	immuneLymphnodesCmd.AddCommand(immuneLymphnodesListCmd)
	immuneLymphnodesCmd.AddCommand(immuneLymphnodesStatusCmd)

	// Cytokines subcommands
	immuneCytokinesCmd.AddCommand(immuneCytokinesStreamCmd)

	// Global flags
	immuneCmd.PersistentFlags().StringVar(&immuneServer, "server", "", "Immune Core server address (default: env VCLI_IMMUNE_ENDPOINT or localhost:50052)")
	immuneCmd.PersistentFlags().StringVarP(&outputFormat, "output", "o", "table", "Output format (table|json)")

	// Agent list flags
	immuneAgentsListCmd.Flags().StringVar(&lymphnodeID, "lymphnode", "", "Filter by lymphnode")
	immuneAgentsListCmd.Flags().StringVar(&agentTypeStr, "type", "", "Filter by agent type")
	immuneAgentsListCmd.Flags().StringVar(&agentStateStr, "state", "", "Filter by state")
	immuneAgentsListCmd.Flags().Int32Var(&page, "page", 1, "Page number")
	immuneAgentsListCmd.Flags().Int32Var(&pageSize, "page-size", 20, "Results per page")
	immuneAgentsListCmd.Flags().BoolVar(&includeMetrics, "metrics", false, "Include metrics")

	// Agent get flags
	immuneAgentsGetCmd.Flags().BoolVar(&includeMetrics, "metrics", false, "Include metrics")
	immuneAgentsGetCmd.Flags().BoolVar(&includeHistory, "history", false, "Include history")

	// Agent clone flags
	immuneAgentsCloneCmd.Flags().Int32Var(&cloneCount, "count", 1, "Number of clones")
	immuneAgentsCloneCmd.Flags().StringVar(&lymphnodeID, "lymphnode", "", "Target lymphnode")

	// Agent terminate flags
	immuneAgentsTerminateCmd.Flags().BoolVar(&terminateGraceful, "graceful", true, "Graceful shutdown")
	immuneAgentsTerminateCmd.Flags().StringVar(&terminateReason, "reason", "", "Termination reason")

	// Lymphnodes flags
	immuneLymphnodesListCmd.Flags().StringVar(&zone, "zone", "", "Filter by zone")
	immuneLymphnodesListCmd.Flags().BoolVar(&includeMetrics, "metrics", false, "Include metrics")

	// Cytokines flags
	immuneCytokinesStreamCmd.Flags().StringSliceVar(&cytokineTopics, "topics", []string{}, "Kafka topics")
	immuneCytokinesStreamCmd.Flags().StringVar(&lymphnodeID, "lymphnode", "", "Filter by lymphnode")
	immuneCytokinesStreamCmd.Flags().StringVar(&cytokineEventType, "event-type", "", "Filter by event type")
	immuneCytokinesStreamCmd.Flags().Int32Var(&cytokineSeverityMin, "severity", 0, "Min severity (1-10)")

	// Health flags
	immuneHealthCmd.Flags().Bool("all", false, "Include all lymphnode details")
}
