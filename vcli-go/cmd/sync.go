package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/cache"
)

// Sync command flags
var (
	syncCachePath string
	syncFull      bool
	syncStrategy  string
)

// syncCmd represents the sync command
var syncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Sync cache for offline mode",
	Long: `Sync and manage local cache for offline operation.

The sync command prefetches data from backend services and stores
it in a local BadgerDB cache. This enables offline mode where vCLI
can operate without network connectivity.

Cache Strategies:
  hot   - Frequently accessed data (5min TTL)
          - Active agents, lymphnode status, pending decisions
  warm  - Moderately accessed data (1h TTL)
          - Agent lists, decision history, metrics summaries
  cold  - Rarely accessed data (24h TTL)
          - Service configs, endpoint discovery

Examples:
  # Full cache sync (all strategies)
  vcli sync --full

  # Sync specific strategy
  vcli sync --strategy hot

  # Clear cache
  vcli sync clear

  # Show cache stats
  vcli sync stats

  # List cached keys
  vcli sync list`,
}

// ============================================================
// Sync Full
// ============================================================

var syncFullCmd = &cobra.Command{
	Use:   "full",
	Short: "Full cache sync (all strategies)",
	RunE:  runSyncFull,
}

func runSyncFull(cmd *cobra.Command, args []string) error {
	// Open cache
	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	fmt.Println("🔄 Starting full cache sync...")

	// Create prefetcher
	prefetcher := cache.NewPrefetcher(c)

	// Execute all strategies
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	if err := prefetcher.PrefetchAll(ctx); err != nil {
		return fmt.Errorf("sync failed: %w", err)
	}

	// Show stats
	hits, misses, size, hitRate := c.GetMetrics()
	fmt.Printf("\n✅ Sync complete!\n")
	fmt.Printf("   Cached entries: %d\n", size)
	fmt.Printf("   Hit rate: %.1f%%\n", hitRate)
	fmt.Printf("   Hits: %d, Misses: %d\n", hits, misses)

	return nil
}

// ============================================================
// Sync Strategy
// ============================================================

var syncStrategyCmd = &cobra.Command{
	Use:   "strategy <name>",
	Short: "Sync specific strategy (hot, warm, cold)",
	Args:  cobra.ExactArgs(1),
	RunE:  runSyncStrategy,
}

func runSyncStrategy(cmd *cobra.Command, args []string) error {
	strategyName := args[0]

	// Validate strategy
	var strategy cache.PrefetchStrategy
	switch strategyName {
	case "hot":
		strategy = cache.HotDataStrategy
	case "warm":
		strategy = cache.WarmDataStrategy
	case "cold":
		strategy = cache.ColdDataStrategy
	default:
		return fmt.Errorf("invalid strategy: %s (valid: hot, warm, cold)", strategyName)
	}

	// Open cache
	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	fmt.Printf("🔄 Syncing %s data strategy...\n", strategyName)

	// Create prefetcher
	prefetcher := cache.NewPrefetcher(c)

	// Execute strategy
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	if err := prefetcher.PrefetchStrategy(ctx, strategy); err != nil {
		return fmt.Errorf("sync failed: %w", err)
	}

	fmt.Printf("✅ Synced %s data (%s TTL)\n", strategyName, strategy.TTL)

	return nil
}

// ============================================================
// Cache Stats
// ============================================================

var syncStatsCmd = &cobra.Command{
	Use:   "stats",
	Short: "Show cache statistics",
	RunE:  runSyncStats,
}

func runSyncStats(cmd *cobra.Command, args []string) error {
	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	hits, misses, size, hitRate := c.GetMetrics()

	fmt.Println("📊 Cache Statistics")
	fmt.Printf("   Total entries: %d\n", size)
	fmt.Printf("   Cache hits: %d\n", hits)
	fmt.Printf("   Cache misses: %d\n", misses)
	fmt.Printf("   Hit rate: %.1f%%\n", hitRate)

	return nil
}

// ============================================================
// List Keys
// ============================================================

var syncListCmd = &cobra.Command{
	Use:   "list [prefix]",
	Short: "List cached keys",
	Args:  cobra.MaximumNArgs(1),
	RunE:  runSyncList,
}

func runSyncList(cmd *cobra.Command, args []string) error {
	prefix := ""
	if len(args) > 0 {
		prefix = args[0]
	}

	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	keys, err := c.ListKeys(prefix)
	if err != nil {
		return fmt.Errorf("failed to list keys: %w", err)
	}

	if len(keys) == 0 {
		fmt.Println("No cached keys found")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "KEY\tCATEGORY\tCREATED\tEXPIRES")

	for _, key := range keys {
		info, err := c.GetInfo(key)
		if err != nil {
			continue
		}

		created := info.CreatedAt.Format("15:04:05")
		expires := info.ExpiresAt.Format("15:04:05")

		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
			truncate(key, 50),
			info.Category,
			created,
			expires,
		)
	}
	w.Flush()

	fmt.Printf("\nTotal: %d keys\n", len(keys))

	return nil
}

// ============================================================
// Clear Cache
// ============================================================

var syncClearCmd = &cobra.Command{
	Use:   "clear",
	Short: "Clear all cached data",
	RunE:  runSyncClear,
}

func runSyncClear(cmd *cobra.Command, args []string) error {
	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	if err := c.Clear(); err != nil {
		return fmt.Errorf("failed to clear cache: %w", err)
	}

	fmt.Println("✅ Cache cleared")

	return nil
}

// ============================================================
// Invalidate Pattern
// ============================================================

var syncInvalidateCmd = &cobra.Command{
	Use:   "invalidate <pattern>",
	Short: "Invalidate cache entries matching pattern",
	Long: `Invalidate cache entries matching a specific pattern.

Patterns:
  agents      - All agent data
  lymphnodes  - All lymphnode data
  decisions   - All decision data
  metrics     - All metrics data
  gateway     - All gateway data

Examples:
  # Invalidate all agent data
  vcli sync invalidate agents

  # Invalidate all metrics
  vcli sync invalidate metrics`,
	Args: cobra.ExactArgs(1),
	RunE: runSyncInvalidate,
}

func runSyncInvalidate(cmd *cobra.Command, args []string) error {
	patternName := args[0]

	var pattern cache.InvalidatePattern
	switch patternName {
	case "agents":
		pattern = cache.InvalidateAllAgents
	case "lymphnodes":
		pattern = cache.InvalidateAllLymphnodes
	case "decisions":
		pattern = cache.InvalidateAllDecisions
	case "metrics":
		pattern = cache.InvalidateAllMetrics
	case "gateway":
		pattern = cache.InvalidateAllGateway
	default:
		return fmt.Errorf("invalid pattern: %s", patternName)
	}

	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	if err := c.Invalidate(pattern); err != nil {
		return fmt.Errorf("failed to invalidate: %w", err)
	}

	fmt.Printf("✅ Invalidated all %s cache entries\n", patternName)

	return nil
}

// ============================================================
// GC
// ============================================================

var syncGCCmd = &cobra.Command{
	Use:   "gc",
	Short: "Run garbage collection on cache",
	RunE:  runSyncGC,
}

func runSyncGC(cmd *cobra.Command, args []string) error {
	c, err := openCache()
	if err != nil {
		return err
	}
	defer c.Close()

	fmt.Println("🗑️  Running garbage collection...")

	if err := c.RunGC(); err != nil {
		return fmt.Errorf("GC failed: %w", err)
	}

	fmt.Println("✅ Garbage collection complete")

	return nil
}

// ============================================================
// Helper Functions
// ============================================================

func openCache() (*cache.Cache, error) {
	// Default cache path
	if syncCachePath == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("failed to get home directory: %w", err)
		}
		syncCachePath = filepath.Join(home, ".vcli")
	}

	c, err := cache.NewCache(syncCachePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open cache: %w", err)
	}

	return c, nil
}

func init() {
	rootCmd.AddCommand(syncCmd)

	// Subcommands
	syncCmd.AddCommand(syncFullCmd)
	syncCmd.AddCommand(syncStrategyCmd)
	syncCmd.AddCommand(syncStatsCmd)
	syncCmd.AddCommand(syncListCmd)
	syncCmd.AddCommand(syncClearCmd)
	syncCmd.AddCommand(syncInvalidateCmd)
	syncCmd.AddCommand(syncGCCmd)

	// Flags
	syncCmd.PersistentFlags().StringVar(&syncCachePath, "cache-path", "", "Cache directory path (default: ~/.vcli)")
}
