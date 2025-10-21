package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/verticedev/coagulation/regulation"
)

const (
	defaultPort    = "8053"
	defaultNATSURL = "nats://nats-jetstream:4222"
)

func main() {
	// Configuration from environment
	port := os.Getenv("PORT")
	if port == "" {
		port = defaultPort
	}

	natsURL := os.Getenv("NATS_URL")
	if natsURL == "" {
		natsURL = defaultNATSURL
	}

	// Initialize Protein C Service
	fmt.Printf("🩸 Starting Protein C Service (Context-Aware Regulation)...\n")
	fmt.Printf("   Port: %s\n", port)
	fmt.Printf("   NATS: %s\n", natsURL)

	service, err := regulation.NewProteinCService(natsURL)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to initialize Protein C service: %v\n", err)
		os.Exit(1)
	}

	// Start service
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := service.Start(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to start Protein C service: %v\n", err)
		os.Exit(1)
	}

	// HTTP server for health checks and metrics
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"healthy","service":"protein-c","timestamp":"%s"}`, time.Now().Format(time.RFC3339))
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"service":"protein-c","context_evaluations":0,"regulations_applied":0}`)
	})

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	// Start HTTP server in goroutine
	go func() {
		fmt.Printf("✅ Protein C Service listening on :%s\n", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "❌ HTTP server error: %v\n", err)
		}
	}()

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n👋 Shutting down Protein C Service...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		fmt.Fprintf(os.Stderr, "❌ HTTP server shutdown error: %v\n", err)
	}

	service.Stop()
	fmt.Println("🛑 Protein C Service stopped")
}
