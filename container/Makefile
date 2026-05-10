# Makefile for NSZ Docker builds
#
# This Makefile provides convenience targets for building and managing
# NSZ Docker images using the build script

# Default image configuration
IMAGE_NAME ?= nsz-tool
DOCKER_REGISTRY ?=
PROD_KEYS_PATH ?= ~/.switch/prod.keys

# Help target (default)
.PHONY: help
help: ## Show this help message
	@echo "🏗️  NSZ Docker Build Targets"
	@echo "================================"
	@echo ""
	@echo "🔧 Configuration Variables:"
	@echo "  IMAGE_NAME=$(IMAGE_NAME)"
	@echo "  DOCKER_REGISTRY=$(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY),<not set>)"
	@echo "  PROD_KEYS_PATH=$(PROD_KEYS_PATH)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Build Targets

.PHONY: build
build: ## Build NSZ image (requires DOCKER_REGISTRY for multi-arch)
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "❌ DOCKER_REGISTRY environment variable is required for multi-arch builds"; \
		echo "💡 Usage: make build DOCKER_REGISTRY=registry.com/namespace"; \
		echo "💡 For single-arch testing: make build-single-arch"; \
		exit 1; \
	fi
	@echo "🔧 Building NSZ image..."
	@DOCKER_REGISTRY=$(DOCKER_REGISTRY) PUSH_TO_REGISTRY=false ./build.sh

.PHONY: build-single-arch
build-single-arch: ## Build for current platform only (faster for testing)
	@echo "🔧 Building NSZ image for current platform only..."
	@./build.sh --single-arch

##@ Registry Operations

.PHONY: push
push: ## Push image to registry (requires DOCKER_REGISTRY)
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "❌ DOCKER_REGISTRY environment variable is required"; \
		echo "💡 Usage: make push DOCKER_REGISTRY=your-registry.com"; \
		echo "💡 Or: DOCKER_REGISTRY=your-registry.com make push"; \
		exit 1; \
	fi
	@echo "📤 Pushing image to $(DOCKER_REGISTRY)..."
	@DOCKER_REGISTRY=$(DOCKER_REGISTRY) PUSH_TO_REGISTRY=true ./build.sh
	@echo "✅ Image pushed successfully!"

.PHONY: buildAndPush
buildAndPush: build push ## Build and push image to registry (requires DOCKER_REGISTRY)
	@echo "🎯 Build and push completed successfully!"

##@ Utility Targets

.PHONY: clean
clean: ## Remove built images from local Docker
	@echo "🧹 Cleaning local NSZ images..."
	@docker rmi $(IMAGE_NAME):latest 2>/dev/null || true
	@echo "✅ Local images cleaned"

.PHONY: clean-dangling
clean-dangling: ## Remove dangling (untagged) images
	@echo "🧹 Cleaning dangling images..."
	@docker image prune -f
	@echo "✅ Dangling images cleaned"

.PHONY: clean-all
clean-all: clean clean-dangling ## Remove all NSZ images and dangling images
	@echo "🧹 Full cleanup completed"

.PHONY: inspect
inspect: ## Show information about built images
	@echo "📋 Local NSZ Images:"
	@docker images $(IMAGE_NAME) || echo "No images found"


##@ Development

.PHONY: setup-alias
setup-alias: ## Show commands to setup shell function (use PROD_KEYS_PATH to customize)
	@echo "🔧 To setup shell function, add these lines to your ~/.bashrc or ~/.zshrc:"
	@echo ""
	@echo "nsz() {"
	@echo "    docker run --rm -v \"\$$(pwd)\":/data -v \"$(PROD_KEYS_PATH)\":/root/.switch/prod.keys $(IMAGE_NAME):latest \"\$$@\""
	@echo "}"
	@echo ""
	@echo "💡 Customize the keys path by setting PROD_KEYS_PATH:"
	@echo "   make setup-alias PROD_KEYS_PATH=/path/to/your/prod.keys"
	@echo ""
	@echo "Then reload your shell or run: source ~/.bashrc"

##@ Information

.PHONY: status
status: ## Show current build status and available images
	@echo "📊 NSZ Docker Build Status"
	@echo "========================="
	@echo "Current directory: $(shell pwd)"
	@echo "Registry: $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY),<not set>)"
	@echo ""
	@echo "Available local images:"
	@docker images $(IMAGE_NAME) 2>/dev/null || echo "  No NSZ images found locally"
	@echo ""
	@echo "Available build files:"
	@ls -la . | grep -E '\.(sh|Dockerfile)'

# Default target
.DEFAULT_GOAL := help