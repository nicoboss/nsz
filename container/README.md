# NSZ Docker Container

Docker containerization for NSZ (Nintendo Switch compression tool) with multi-architecture support and optimized image size.

## Build vs Push Behavior

- **`build`** targets: Only build images (multi-architecture), do not push to registry
- **`push`** targets: Only push already-built images to registry
- **`buildAndPush`** targets: Combined operation that builds then pushes in sequence

## Quick Start

### Build Images

```bash
# Build NSZ image (optimized, ~88MB) - requires registry for multi-arch
make build DOCKER_REGISTRY=docker.io/username

# For local testing only (single architecture)
make build-single-arch
```

### Push to Registry

```bash
# Push image to registry (must be built first)
make push DOCKER_REGISTRY=docker.io/username
```

### Build and Push (Combined)

```bash
# Build and push image in one command
make buildAndPush DOCKER_REGISTRY=docker.io/username
```

## Configuration

Set these variables to customize the build:

```bash
IMAGE_NAME=nsz-tool                          # Default image name
DOCKER_REGISTRY=registry.com/namespace       # Registry + namespace for multi-arch builds
PROD_KEYS_PATH=~/.switch/prod.keys           # Path to Nintendo Switch keys
```

### Registry Format

The `DOCKER_REGISTRY` must include both registry and namespace:

```bash
# Docker Hub
DOCKER_REGISTRY=docker.io/username

# GitHub Container Registry
DOCKER_REGISTRY=ghcr.io/username

# Custom registry
DOCKER_REGISTRY=your-registry.com/namespace

# Harbor registry
DOCKER_REGISTRY=harbor.company.com/project
```

## Available Images

| Image Variant | Size  | Description |
|---------------|-------|-------------|
| `nsz-tool:latest` | ~88MB | CLI-only, optimized with Alpine Linux |

## Architecture Support

Multi-architecture builds support:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit)
- `linux/arm/v7` (ARM 32-bit)
- `linux/ppc64le` (PowerPC 64-bit LE)

## Usage Examples

### Direct Docker Usage

```bash
# Run NSZ with keys mounted
docker run --rm \
  -v "$(pwd)":/data \
  -v "$HOME/.switch/prod.keys":/root/.switch/prod.keys \
  nsz-tool:latest game.nsp

# Decompress NSZ file
docker run --rm \
  -v "$(pwd)":/data \
  -v "$HOME/.switch/prod.keys":/root/.switch/prod.keys \
  nsz-tool:latest -D game.nsz
```

### Shell Function Setup

Get personalized shell function command:

```bash
# Default keys path (~/.switch/prod.keys)
make setup-alias

# Custom keys path
make setup-alias PROD_KEYS_PATH=/path/to/your/prod.keys
```

Then add the generated function to your `~/.bashrc` or `~/.zshrc`:

```bash
nsz() {
    docker run --rm -v "$(pwd)":/data -v "$HOME/.switch/prod.keys":/root/.switch/prod.keys nsz-tool:latest "$@"
}
```

After that, use NSZ like a native command:

```bash
nsz game.nsp          # Compress NSP to NSZ
nsz -D game.nsz       # Decompress NSZ to NSP
nsz --help            # Show help
```

## Build Options

### Local Development

```bash
# Single-architecture build (faster for testing) - no registry required
make build-single-arch

# Verbose build output with registry
VERBOSE=true make build DOCKER_REGISTRY=docker.io/username
```

### Registry Deployment

For multi-architecture builds, you have two approaches:

**Approach 1: Build then Push (separate steps)**
```bash
# First build the image
make build DOCKER_REGISTRY=docker.io/username

# Then push it
make push DOCKER_REGISTRY=docker.io/username
```

**Approach 2: Build and Push (combined)**
```bash
# Build and push in one command
make buildAndPush DOCKER_REGISTRY=docker.io/username
```

## Available Targets

| Target | Description |
|--------|-------------|
| `build` | Build NSZ image (requires DOCKER_REGISTRY for multi-arch) |
| `build-single-arch` | Build for current platform only (faster for testing) |
| `push` | Push image to registry (requires DOCKER_REGISTRY) |
| `buildAndPush` | Build and push image to registry (requires DOCKER_REGISTRY) |
| `clean` | Remove built images from local Docker |
| `clean-dangling` | Remove dangling (untagged) images |
| `clean-all` | Remove all NSZ and dangling images |
| `inspect` | Show information about built images |
| `setup-alias` | Show commands to setup shell function (use PROD_KEYS_PATH to customize) |
| `status` | Show current build status and available images |
| `help` | Show all targets |

## Files Structure

```
container/
├── Dockerfile          # CLI-optimized image (~88MB)
├── build.sh            # Multi-architecture build script
├── Makefile            # Build automation
└── README.md           # This file
```

## Requirements

- Docker with buildx support
- For multi-arch: Docker registry access
- For NSZ usage: Nintendo Switch `prod.keys` file

## Nintendo Switch Keys

NSZ requires a `prod.keys` file containing Nintendo Switch encryption keys. This file is not included and must be obtained legally from your own Nintendo Switch console.

Mount your keys file to one of these container paths:
- `/root/.switch/prod.keys` (recommended)
- `/usr/local/bin/keys.txt` (alternative)

## Advanced Usage

### Custom Build Script

```bash
cd container/

# CLI version with registry push
DOCKER_REGISTRY=your-registry.com ./build.sh

# Single architecture only
./build.sh --single-arch

# Verbose output
./build.sh --verbose
```

### Environment Variables

```bash
# Set defaults for your environment
export DOCKER_REGISTRY=docker.io/yourusername
export PROD_KEYS_PATH=/secure/nintendo/prod.keys
export IMAGE_NAME=my-nsz-tool

# Then use normally
make build         # Uses DOCKER_REGISTRY from environment
make push          # Uses DOCKER_REGISTRY from environment
make buildAndPush  # Build and push in one command
```