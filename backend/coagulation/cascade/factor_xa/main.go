package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/verticedev/coagulation/cascade"
)

const (
	defaultPort    = "8050"
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

	// Initialize Factor Xa Service
	fmt.Printf("🩸 Starting Factor Xa Service...\n")
	fmt.Printf("   Port: %s\n", port)
	fmt.Printf("   NATS: %s\n", natsURL)

	service, err := cascade.NewFactorXaService(natsURL)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to initialize Factor Xa service: %v\n", err)
		os.Exit(1)
	}

	// Start service
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := service.Start(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to start Factor Xa service: %v\n", err)
		os.Exit(1)
	}

	// HTTP server for health checks and metrics
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"healthy","service":"factor-xa","timestamp":"%s"}`, time.Now().Format(time.RFC3339))
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		// TODO: Implement metrics export
		fmt.Fprintf(w, `{"service":"factor-xa","active_quarantines":0}`)
	})

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	// Start HTTP server in goroutine
	go func() {
		fmt.Printf("✅ Factor Xa Service listening on :%s\n", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "❌ HTTP server error: %v\n", err)
		}
	}()

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n👋 Shutting down Factor Xa Service...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		fmt.Fprintf(os.Stderr, "❌ HTTP server shutdown error: %v\n", err)
	}

	service.Stop()
	fmt.Println("🛑 Factor Xa Service stopped")
}
