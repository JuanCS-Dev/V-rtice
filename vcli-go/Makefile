.PHONY: build test lint clean bench coverage install help

# Variables
BINARY_NAME=vcli
VERSION?=0.1.0
BUILD_DIR=bin
GO_FILES=$(shell find . -name '*.go' -not -path "./vendor/*")
COVERAGE_FILE=coverage.out

# Default target
.DEFAULT_GOAL := help

## build: Build the binary
build:
	@echo "🔨 Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(BINARY_NAME) -ldflags="-X main.Version=$(VERSION)" ./cmd/root.go
	@echo "✅ Built: $(BUILD_DIR)/$(BINARY_NAME)"

## install: Install the binary to $GOPATH/bin
install:
	@echo "📦 Installing $(BINARY_NAME)..."
	go install -ldflags="-X main.Version=$(VERSION)" ./cmd/root.go
	@echo "✅ Installed to $$(go env GOPATH)/bin/$(BINARY_NAME)"

## test: Run all tests
test:
	@echo "🧪 Running tests..."
	go test ./... -v -race -timeout 30s
	@echo "✅ All tests passed"

## test-short: Run short tests only
test-short:
	@echo "🧪 Running short tests..."
	go test ./... -v -short
	@echo "✅ Short tests passed"

## bench: Run benchmarks
bench:
	@echo "📊 Running benchmarks..."
	go test ./... -bench=. -benchmem -run=^$$
	@echo "✅ Benchmarks complete"

## coverage: Generate test coverage report
coverage:
	@echo "📈 Generating coverage report..."
	go test ./... -coverprofile=$(COVERAGE_FILE) -covermode=atomic
	go tool cover -html=$(COVERAGE_FILE) -o coverage.html
	@echo "✅ Coverage report: coverage.html"
	@echo "📊 Coverage summary:"
	@go tool cover -func=$(COVERAGE_FILE) | tail -1

## lint: Run linter
lint:
	@echo "🔍 Running linter..."
	@which golangci-lint > /dev/null || (echo "❌ golangci-lint not installed. Run: curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $$(go env GOPATH)/bin v1.55.2" && exit 1)
	golangci-lint run --timeout 5m
	@echo "✅ Lint passed"

## fmt: Format code
fmt:
	@echo "🎨 Formatting code..."
	gofmt -w $(GO_FILES)
	goimports -w $(GO_FILES)
	@echo "✅ Code formatted"

## vet: Run go vet
vet:
	@echo "🔬 Running go vet..."
	go vet ./...
	@echo "✅ Vet passed"

## security: Run security checks
security:
	@echo "🛡️ Running security checks..."
	@which gosec > /dev/null || (echo "❌ gosec not installed. Run: go install github.com/securego/gosec/v2/cmd/gosec@latest" && exit 1)
	gosec -quiet ./...
	@echo "✅ Security checks passed"

## mod-tidy: Tidy go modules
mod-tidy:
	@echo "🧹 Tidying modules..."
	go mod tidy
	@echo "✅ Modules tidied"

## mod-download: Download dependencies
mod-download:
	@echo "📥 Downloading dependencies..."
	go mod download
	@echo "✅ Dependencies downloaded"

## clean: Clean build artifacts
clean:
	@echo "🧹 Cleaning..."
	rm -rf $(BUILD_DIR)
	rm -f $(COVERAGE_FILE) coverage.html
	go clean
	@echo "✅ Clean complete"

## clean-all: Clean everything including modules
clean-all: clean
	@echo "🧹 Deep cleaning..."
	go clean -modcache
	@echo "✅ Deep clean complete"

## run: Build and run
run: build
	@echo "🚀 Running $(BINARY_NAME)..."
	./$(BUILD_DIR)/$(BINARY_NAME)

## dev: Run in development mode with hot reload
dev:
	@echo "🔄 Running in dev mode..."
	@which air > /dev/null || (echo "❌ air not installed. Run: go install github.com/cosmtrek/air@latest" && exit 1)
	air

## docker-build: Build Docker image
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(BINARY_NAME):$(VERSION) .
	@echo "✅ Docker image built: $(BINARY_NAME):$(VERSION)"

## docker-run: Run Docker container
docker-run:
	@echo "🐳 Running Docker container..."
	docker run -it --rm $(BINARY_NAME):$(VERSION)

## ci: Run CI pipeline locally
ci: lint test security
	@echo "✅ CI pipeline passed"

## release: Create release build for multiple platforms
release:
	@echo "🚀 Building release binaries..."
	@mkdir -p $(BUILD_DIR)/release
	GOOS=linux GOARCH=amd64 go build -o $(BUILD_DIR)/release/$(BINARY_NAME)-linux-amd64 -ldflags="-X main.Version=$(VERSION) -s -w" ./cmd/root.go
	GOOS=linux GOARCH=arm64 go build -o $(BUILD_DIR)/release/$(BINARY_NAME)-linux-arm64 -ldflags="-X main.Version=$(VERSION) -s -w" ./cmd/root.go
	GOOS=darwin GOARCH=amd64 go build -o $(BUILD_DIR)/release/$(BINARY_NAME)-darwin-amd64 -ldflags="-X main.Version=$(VERSION) -s -w" ./cmd/root.go
	GOOS=darwin GOARCH=arm64 go build -o $(BUILD_DIR)/release/$(BINARY_NAME)-darwin-arm64 -ldflags="-X main.Version=$(VERSION) -s -w" ./cmd/root.go
	GOOS=windows GOARCH=amd64 go build -o $(BUILD_DIR)/release/$(BINARY_NAME)-windows-amd64.exe -ldflags="-X main.Version=$(VERSION) -s -w" ./cmd/root.go
	@echo "✅ Release binaries built in $(BUILD_DIR)/release/"
	@ls -lh $(BUILD_DIR)/release/

## help: Show this help message
help:
	@echo "📚 Vértice CLI 2.0 - Makefile Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/  /'
	@echo ""
	@echo "Examples:"
	@echo "  make build          # Build the binary"
	@echo "  make test           # Run tests"
	@echo "  make ci             # Run full CI pipeline"
	@echo "  make release        # Create multi-platform release"
