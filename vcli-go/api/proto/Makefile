# gRPC Code Generation Makefile

.PHONY: all clean install-deps generate

all: generate

# Install required Go plugins for protoc
install-deps:
	@echo "📦 Installing protoc-gen-go and protoc-gen-go-grpc..."
	go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
	go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
	@echo "✅ Dependencies installed"

# Generate Go code from proto files
generate:
	@echo "🔨 Generating Go code from proto definitions..."
	@mkdir -p ../grpc/governance
	protoc --go_out=../grpc --go_opt=paths=source_relative \
		--go-grpc_out=../grpc --go-grpc_opt=paths=source_relative \
		governance.proto
	@echo "✅ Code generation complete"
	@echo "📁 Generated files in: vcli-go/api/grpc/governance/"

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf ../grpc/governance/*.pb.go
	@echo "✅ Cleaned"

# Help
help:
	@echo "Available targets:"
	@echo "  install-deps  - Install protoc Go plugins"
	@echo "  generate      - Generate Go code from .proto files"
	@echo "  clean         - Remove generated files"
	@echo "  all           - Run generate (default)"
