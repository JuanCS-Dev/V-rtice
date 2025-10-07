package main

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/immunis"
)

var (
	// Immunis service endpoints
	macrophageEndpoint  string
	bcellEndpoint       string
	helperTEndpoint     string
	cytotoxicTEndpoint  string
	lymphnodeEndpoint   string
	immunisToken        string

	// Macrophage flags
	sampleFile     string
	malwareFamily  string
	artifactFile   string

	// Lymphnode flags
	cloneAgentID        string
	cloneEspecializacao string
	cloneNumClones      int
	cloneMutate         bool
	cloneMutationRate   float64

	// Generic flags for immunis (reuse from maximus.go)
	// dataFile and contextFile are already declared in maximus.go
)

// immunisCmd represents the immunis command
var immunisCmd = &cobra.Command{
	Use:   "immunis",
	Short: "Interact with Immunis System (Adaptive Immunity)",
	Long: `Immunis System - Bio-inspired adaptive immune response.

The Immunis system provides adaptive immunity through specialized cell types:
- Macrophage: Malware phagocytosis and analysis
- B-Cell: Antibody generation
- Helper T-Cell: Immune coordination
- Cytotoxic T-Cell: Threat elimination

Examples:
  # Phagocytose malware sample
  vcli immunis macrophage phagocytose --sample malware.bin --family ransomware

  # Generate antibodies
  vcli immunis bcell process --data-file threat.json

  # Coordinate immune response
  vcli immunis helper-t process --data-file signals.json

  # Eliminate threat
  vcli immunis cytotoxic-t process --data-file target.json`,
}

// ============================================================================
// MACROPHAGE COMMANDS
// ============================================================================

var macrophageCmd = &cobra.Command{
	Use:   "macrophage",
	Short: "Macrophage - Malware phagocytosis and analysis",
	Long: `Macrophage Service for malware phagocytosis.

Bio-inspired malware analysis:
- Engulfs malicious samples
- Analyzes via Cuckoo Sandbox
- Extracts IOCs and generates YARA signatures
- Presents antigens to Dendritic Cells`,
}

var macrophagePhagocytoseCmd = &cobra.Command{
	Use:   "phagocytose",
	Short: "Phagocytose (analyze) malware sample",
	RunE:  runMacrophagePhagocytose,
}

func runMacrophagePhagocytose(cmd *cobra.Command, args []string) error {
	if sampleFile == "" {
		return fmt.Errorf("--sample is required")
	}

	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.Phagocytose(sampleFile, malwareFamily)
	if err != nil {
		return fmt.Errorf("phagocytose failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var macrophagePresentAntigenCmd = &cobra.Command{
	Use:   "present-antigen",
	Short: "Present antigen to Dendritic Cells",
	RunE:  runMacrophagePresentAntigen,
}

func runMacrophagePresentAntigen(cmd *cobra.Command, args []string) error {
	if artifactFile == "" {
		return fmt.Errorf("--artifact is required")
	}

	artifact, err := readJSONFile(artifactFile)
	if err != nil {
		return fmt.Errorf("failed to read artifact: %w", err)
	}

	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.PresentAntigen(artifact)
	if err != nil {
		return fmt.Errorf("present antigen failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var macrophageCleanupCmd = &cobra.Command{
	Use:   "cleanup",
	Short: "Cleanup old artifacts",
	RunE:  runMacrophageCleanup,
}

func runMacrophageCleanup(cmd *cobra.Command, args []string) error {
	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.Cleanup()
	if err != nil {
		return fmt.Errorf("cleanup failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var macrophageStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get Macrophage service status",
	RunE:  runMacrophageStatus,
}

func runMacrophageStatus(cmd *cobra.Command, args []string) error {
	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("status check failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var macrophageHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Macrophage service health",
	RunE:  runMacrophageHealth,
}

func runMacrophageHealth(cmd *cobra.Command, args []string) error {
	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Service)
	fmt.Printf("Cuckoo Enabled: %v\n", resp.CuckooEnabled)
	fmt.Printf("Kafka Enabled: %v\n", resp.KafkaEnabled)
	fmt.Printf("Artifacts: %d\n", resp.ArtifactsCount)
	fmt.Printf("Signatures: %d\n", resp.SignaturesCount)
	return nil
}

var macrophageArtifactsCmd = &cobra.Command{
	Use:   "artifacts",
	Short: "List processed artifacts",
	RunE:  runMacrophageArtifacts,
}

func runMacrophageArtifacts(cmd *cobra.Command, args []string) error {
	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.GetArtifacts()
	if err != nil {
		return fmt.Errorf("failed to get artifacts: %w", err)
	}

	printJSON(resp)
	return nil
}

var macrophageSignaturesCmd = &cobra.Command{
	Use:   "signatures",
	Short: "List generated YARA signatures",
	RunE:  runMacrophageSignatures,
}

func runMacrophageSignatures(cmd *cobra.Command, args []string) error {
	client := immunis.NewMacrophageClient(macrophageEndpoint, immunisToken)
	resp, err := client.GetSignatures()
	if err != nil {
		return fmt.Errorf("failed to get signatures: %w", err)
	}

	printJSON(resp)
	return nil
}

// ============================================================================
// B-CELL COMMANDS
// ============================================================================

var bcellCmd = &cobra.Command{
	Use:   "bcell",
	Short: "B-Cell - Antibody generation",
	Long: `B-Cell Service for antibody generation.

Bio-inspired adaptive immunity:
- Processes threat information
- Generates specific antibodies
- Adaptive immune response`,
}

var bcellProcessCmd = &cobra.Command{
	Use:   "process",
	Short: "Process threat data and generate antibodies",
	RunE:  runBCellProcess,
}

func runBCellProcess(cmd *cobra.Command, args []string) error {
	if dataFile == "" {
		return fmt.Errorf("--data-file is required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data: %w", err)
	}

	var context map[string]interface{}
	if contextFile != "" {
		context, err = readJSONFile(contextFile)
		if err != nil {
			return fmt.Errorf("failed to read context: %w", err)
		}
	}

	client := immunis.NewBCellClient(bcellEndpoint, immunisToken)
	resp, err := client.Process(data, context)
	if err != nil {
		return fmt.Errorf("process failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var bcellHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check B-Cell service health",
	RunE:  runBCellHealth,
}

func runBCellHealth(cmd *cobra.Command, args []string) error {
	client := immunis.NewBCellClient(bcellEndpoint, immunisToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Service)
	fmt.Printf("Core Available: %v\n", resp.CoreAvailable)
	return nil
}

var bcellStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get B-Cell service status",
	RunE:  runBCellStatus,
}

func runBCellStatus(cmd *cobra.Command, args []string) error {
	client := immunis.NewBCellClient(bcellEndpoint, immunisToken)
	resp, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("status check failed: %w", err)
	}

	printJSON(resp)
	return nil
}

// ============================================================================
// HELPER T-CELL COMMANDS
// ============================================================================

var helperTCmd = &cobra.Command{
	Use:   "helper-t",
	Short: "Helper T-Cell - Immune coordination",
	Long: `Helper T-Cell Service for immune coordination.

Bio-inspired immune system coordination:
- Coordinates immune responses
- Activates other immune cells
- Regulates immune activity`,
}

var helperTProcessCmd = &cobra.Command{
	Use:   "process",
	Short: "Process coordination signals",
	RunE:  runHelperTProcess,
}

func runHelperTProcess(cmd *cobra.Command, args []string) error {
	if dataFile == "" {
		return fmt.Errorf("--data-file is required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data: %w", err)
	}

	var context map[string]interface{}
	if contextFile != "" {
		context, err = readJSONFile(contextFile)
		if err != nil {
			return fmt.Errorf("failed to read context: %w", err)
		}
	}

	client := immunis.NewHelperTClient(helperTEndpoint, immunisToken)
	resp, err := client.Process(data, context)
	if err != nil {
		return fmt.Errorf("process failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var helperTHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Helper T-Cell service health",
	RunE:  runHelperTHealth,
}

func runHelperTHealth(cmd *cobra.Command, args []string) error {
	client := immunis.NewHelperTClient(helperTEndpoint, immunisToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Service)
	fmt.Printf("Core Available: %v\n", resp.CoreAvailable)
	return nil
}

var helperTStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get Helper T-Cell service status",
	RunE:  runHelperTStatus,
}

func runHelperTStatus(cmd *cobra.Command, args []string) error {
	client := immunis.NewHelperTClient(helperTEndpoint, immunisToken)
	resp, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("status check failed: %w", err)
	}

	printJSON(resp)
	return nil
}

// ============================================================================
// CYTOTOXIC T-CELL COMMANDS
// ============================================================================

var cytotoxicTCmd = &cobra.Command{
	Use:   "cytotoxic-t",
	Short: "Cytotoxic T-Cell - Threat elimination",
	Long: `Cytotoxic T-Cell Service for threat elimination.

Bio-inspired threat elimination:
- Identifies infected/compromised targets
- Eliminates threats
- Direct immune response`,
}

var cytotoxicTProcessCmd = &cobra.Command{
	Use:   "process",
	Short: "Process elimination targets",
	RunE:  runCytotoxicTProcess,
}

func runCytotoxicTProcess(cmd *cobra.Command, args []string) error {
	if dataFile == "" {
		return fmt.Errorf("--data-file is required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data: %w", err)
	}

	var context map[string]interface{}
	if contextFile != "" {
		context, err = readJSONFile(contextFile)
		if err != nil {
			return fmt.Errorf("failed to read context: %w", err)
		}
	}

	client := immunis.NewCytotoxicTClient(cytotoxicTEndpoint, immunisToken)
	resp, err := client.Process(data, context)
	if err != nil {
		return fmt.Errorf("process failed: %w", err)
	}

	printJSON(resp)
	return nil
}

var cytotoxicTHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Cytotoxic T-Cell service health",
	RunE:  runCytotoxicTHealth,
}

func runCytotoxicTHealth(cmd *cobra.Command, args []string) error {
	client := immunis.NewCytotoxicTClient(cytotoxicTEndpoint, immunisToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Service)
	fmt.Printf("Core Available: %v\n", resp.CoreAvailable)
	return nil
}

var cytotoxicTStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get Cytotoxic T-Cell service status",
	RunE:  runCytotoxicTStatus,
}

func runCytotoxicTStatus(cmd *cobra.Command, args []string) error {
	client := immunis.NewCytotoxicTClient(cytotoxicTEndpoint, immunisToken)
	resp, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("status check failed: %w", err)
	}

	printJSON(resp)
	return nil
}

// ============================================================================
// HELPER FUNCTIONS (readJSONFile and printJSON are in maximus.go)
// ============================================================================

// ============================================================================
// LYMPHNODE COMMANDS
// ============================================================================

var lymphnodeCmd = &cobra.Command{
	Use:   "lymphnode",
	Short: "Lymphnode coordination operations",
	Long:  "Lymphnode operations: clonal expansion, apoptosis, metrics, homeostatic state",
}

var lymphnodeCloneCmd = &cobra.Command{
	Use:   "clone",
	Short: "Clone an agent (clonal expansion)",
	Long:  "Create specialized clones of a high-performing agent to respond to specific threats",
	RunE:  runLymphnodeClone,
}

var lymphnodeDestroyCmd = &cobra.Command{
	Use:   "destroy <especializacao>",
	Short: "Destroy clones by specialization (apoptosis)",
	Long:  "Trigger programmed cell death for all clones with a specific specialization",
	Args:  cobra.ExactArgs(1),
	RunE:  runLymphnodeDestroy,
}

var lymphnodeMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Get lymphnode metrics",
	Long:  "Retrieve lymphnode operational metrics and statistics",
	RunE:  runLymphnodeMetrics,
}

var lymphnodeHomeostaticStateCmd = &cobra.Command{
	Use:   "homeostatic-state",
	Short: "Get homeostatic state",
	Long:  "Retrieve current homeostatic state (REPOUSO, VIGILÂNCIA, ATENÇÃO, ATIVAÇÃO, INFLAMAÇÃO)",
	RunE:  runLymphnodeHomeostaticState,
}

// ============================================================================
// LYMPHNODE COMMAND IMPLEMENTATIONS
// ============================================================================

func runLymphnodeClone(cmd *cobra.Command, args []string) error {
	client := immunis.NewLymphnodeClient(lymphnodeEndpoint, immunisToken)

	req := immunis.CloneRequest{
		AgentID:      cloneAgentID,
		NumClones:    cloneNumClones,
		Mutate:       cloneMutate,
		MutationRate: cloneMutationRate,
	}

	if cloneEspecializacao != "" {
		req.Especializacao = &cloneEspecializacao
	}

	result, err := client.CloneAgent(req)
	if err != nil {
		return fmt.Errorf("failed to clone agent: %w", err)
	}

	printJSON(result)
	return nil
}

func runLymphnodeDestroy(cmd *cobra.Command, args []string) error {
	client := immunis.NewLymphnodeClient(lymphnodeEndpoint, immunisToken)

	result, err := client.DestroyClones(args[0])
	if err != nil {
		return fmt.Errorf("failed to destroy clones: %w", err)
	}

	printJSON(result)
	return nil
}

func runLymphnodeMetrics(cmd *cobra.Command, args []string) error {
	client := immunis.NewLymphnodeClient(lymphnodeEndpoint, immunisToken)

	result, err := client.GetMetrics()
	if err != nil {
		return fmt.Errorf("failed to get metrics: %w", err)
	}

	printJSON(result)
	return nil
}

func runLymphnodeHomeostaticState(cmd *cobra.Command, args []string) error {
	client := immunis.NewLymphnodeClient(lymphnodeEndpoint, immunisToken)

	result, err := client.GetHomeostaticState()
	if err != nil {
		return fmt.Errorf("failed to get homeostatic state: %w", err)
	}

	printJSON(result)
	return nil
}

// ============================================================================
// INIT
// ============================================================================

func init() {
	rootCmd.AddCommand(immunisCmd)

	// Add cell type commands
	immunisCmd.AddCommand(macrophageCmd)
	immunisCmd.AddCommand(bcellCmd)
	immunisCmd.AddCommand(helperTCmd)
	immunisCmd.AddCommand(cytotoxicTCmd)
	immunisCmd.AddCommand(lymphnodeCmd)

	// Macrophage subcommands
	macrophageCmd.AddCommand(macrophagePhagocytoseCmd)
	macrophageCmd.AddCommand(macrophagePresentAntigenCmd)
	macrophageCmd.AddCommand(macrophageCleanupCmd)
	macrophageCmd.AddCommand(macrophageStatusCmd)
	macrophageCmd.AddCommand(macrophageHealthCmd)
	macrophageCmd.AddCommand(macrophageArtifactsCmd)
	macrophageCmd.AddCommand(macrophageSignaturesCmd)

	// B-Cell subcommands
	bcellCmd.AddCommand(bcellProcessCmd)
	bcellCmd.AddCommand(bcellHealthCmd)
	bcellCmd.AddCommand(bcellStatusCmd)

	// Helper T-Cell subcommands
	helperTCmd.AddCommand(helperTProcessCmd)
	helperTCmd.AddCommand(helperTHealthCmd)
	helperTCmd.AddCommand(helperTStatusCmd)

	// Cytotoxic T-Cell subcommands
	cytotoxicTCmd.AddCommand(cytotoxicTProcessCmd)
	cytotoxicTCmd.AddCommand(cytotoxicTHealthCmd)
	cytotoxicTCmd.AddCommand(cytotoxicTStatusCmd)

	// Lymphnode subcommands
	lymphnodeCmd.AddCommand(lymphnodeCloneCmd)
	lymphnodeCmd.AddCommand(lymphnodeDestroyCmd)
	lymphnodeCmd.AddCommand(lymphnodeMetricsCmd)
	lymphnodeCmd.AddCommand(lymphnodeHomeostaticStateCmd)

	// Service endpoints
	macrophageCmd.PersistentFlags().StringVar(&macrophageEndpoint, "macrophage-endpoint", "http://localhost:8030", "Macrophage service endpoint")
	bcellCmd.PersistentFlags().StringVar(&bcellEndpoint, "bcell-endpoint", "http://localhost:8031", "B-Cell service endpoint")
	helperTCmd.PersistentFlags().StringVar(&helperTEndpoint, "helper-t-endpoint", "http://localhost:8032", "Helper T-Cell service endpoint")
	cytotoxicTCmd.PersistentFlags().StringVar(&cytotoxicTEndpoint, "cytotoxic-t-endpoint", "http://localhost:8033", "Cytotoxic T-Cell service endpoint")
	lymphnodeCmd.PersistentFlags().StringVar(&lymphnodeEndpoint, "lymphnode-endpoint", "http://localhost:8034", "Lymphnode service endpoint")

	// Auth tokens
	macrophageCmd.PersistentFlags().StringVar(&immunisToken, "token", "", "Authentication token")
	bcellCmd.PersistentFlags().StringVar(&immunisToken, "token", "", "Authentication token")
	helperTCmd.PersistentFlags().StringVar(&immunisToken, "token", "", "Authentication token")
	cytotoxicTCmd.PersistentFlags().StringVar(&immunisToken, "token", "", "Authentication token")
	lymphnodeCmd.PersistentFlags().StringVar(&immunisToken, "token", "", "Authentication token")

	// Macrophage flags
	macrophagePhagocytoseCmd.Flags().StringVar(&sampleFile, "sample", "", "Malware sample file")
	macrophagePhagocytoseCmd.Flags().StringVar(&malwareFamily, "family", "unknown", "Malware family")
	macrophagePresentAntigenCmd.Flags().StringVar(&artifactFile, "artifact", "", "Artifact file (JSON)")

	// B-Cell flags
	bcellProcessCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	bcellProcessCmd.Flags().StringVar(&contextFile, "context-file", "", "Context file (JSON, optional)")

	// Helper T-Cell flags
	helperTProcessCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	helperTProcessCmd.Flags().StringVar(&contextFile, "context-file", "", "Context file (JSON, optional)")

	// Cytotoxic T-Cell flags
	cytotoxicTProcessCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	cytotoxicTProcessCmd.Flags().StringVar(&contextFile, "context-file", "", "Context file (JSON, optional)")

	// Lymphnode flags
	lymphnodeCloneCmd.Flags().StringVar(&cloneAgentID, "agent-id", "", "ID of agent to clone")
	lymphnodeCloneCmd.Flags().StringVar(&cloneEspecializacao, "especializacao", "", "Specialization for clones (optional)")
	lymphnodeCloneCmd.Flags().IntVar(&cloneNumClones, "num-clones", 1, "Number of clones to create (1-10)")
	lymphnodeCloneCmd.Flags().BoolVar(&cloneMutate, "mutate", true, "Apply somatic hypermutation")
	lymphnodeCloneCmd.Flags().Float64Var(&cloneMutationRate, "mutation-rate", 0.1, "Mutation rate (0.0-1.0)")
	lymphnodeCloneCmd.MarkFlagRequired("agent-id")
}
