// Package main - vCLI 2.0 Entry Point
//
// Lead Architect: Juan Carlos de Souza (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is the main entry point for the Vértice CLI 2.0.
// All command implementations are in the cmd/ directory.
// This file provides the build entry point and main() function.
package main

import (
	"fmt"
	"os"

	"github.com/verticedev/vcli-go/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
