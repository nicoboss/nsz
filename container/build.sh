#!/bin/bash

# Script to build NSZ Docker image with multi-architecture support

set -e

IMAGE_NAME="nsz-tool"
TAG="latest"
PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7,linux/ppc64le"
DOCKERFILE="Dockerfile"
REGISTRY=${DOCKER_REGISTRY:-""}
VERBOSE=${VERBOSE:-false}
PUSH_TO_REGISTRY=${PUSH_TO_REGISTRY:-false}

echo "🏗️  Multi-Architecture Docker Build for NSZ"
echo "================================================"
echo "📦 Image name: $IMAGE_NAME:$TAG"
echo "🏷️  Platforms: $PLATFORMS"
echo "⚡ Building CLI-only version (optimized size)"

# Check if buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo "❌ Docker Buildx is required for multi-architecture builds"
    echo "💡 Please install Docker Desktop or enable buildx"
    exit 1
fi

# Parse arguments
PROGRESS_FLAG="--progress=auto"
if [ "$VERBOSE" = "true" ] || [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
    PROGRESS_FLAG="--progress=plain"
    echo "🔍 Verbose mode enabled"
fi

# Special case: if user explicitly wants single-arch
if [ "$1" = "--single-arch" ]; then
    echo "🔄 Building for current platform only..."
    if [ "$VERBOSE" = "true" ]; then
        docker build -f "$DOCKERFILE" -t "$IMAGE_NAME:$TAG" ../
    else
        docker build -f "$DOCKERFILE" -t "$IMAGE_NAME:$TAG" ../ >/dev/null 2>&1
    fi
    echo "✅ Single-architecture image built successfully!"
else
    # Default: Multi-architecture build
    echo "🔧 Setting up buildx builder..."
    docker buildx create --name nsz-builder --use 2>/dev/null || {
        echo "📋 Using existing builder: nsz-builder"
        docker buildx use nsz-builder
    }

    if [ -n "$REGISTRY" ]; then
        if [ "$PUSH_TO_REGISTRY" = "true" ]; then
            echo ""
            echo "📤 Building and pushing to registry: $REGISTRY/$IMAGE_NAME:$TAG"
            echo "⏳ This may take several minutes for multiple architectures..."

            docker buildx build \
                --platform "$PLATFORMS" \
                --file "$DOCKERFILE" \
                --tag "$REGISTRY/$IMAGE_NAME:$TAG" \
                --push \
                $PROGRESS_FLAG \
                ../

            echo "✅ Multi-architecture image pushed to $REGISTRY/$IMAGE_NAME:$TAG"
            echo ""
            echo "🔍 To inspect the image manifest:"
            echo "  docker buildx imagetools inspect $REGISTRY/$IMAGE_NAME:$TAG"
        else
            echo ""
            echo "🏗️  Building multi-architecture image: $REGISTRY/$IMAGE_NAME:$TAG"
            echo "⏳ This may take several minutes for multiple architectures..."
            echo "💡 Image will be built but not pushed (use PUSH_TO_REGISTRY=true to push)"

            docker buildx build \
                --platform "$PLATFORMS" \
                --file "$DOCKERFILE" \
                --tag "$REGISTRY/$IMAGE_NAME:$TAG" \
                $PROGRESS_FLAG \
                ../

            echo "✅ Multi-architecture image built: $REGISTRY/$IMAGE_NAME:$TAG"
            echo ""
            echo "🔧 Loading current architecture image to local Docker..."

            docker buildx build \
                --platform "$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')" \
                --file "$DOCKERFILE" \
                --tag "$IMAGE_NAME:$TAG" \
                --load \
                $PROGRESS_FLAG \
                ../

            echo "✅ Local image loaded: $IMAGE_NAME:$TAG"
            echo ""
            echo "📋 To push the image:"
            echo "  PUSH_TO_REGISTRY=true DOCKER_REGISTRY=$REGISTRY ./build.sh"
        fi
    else
        echo ""
        echo "⚠️  No DOCKER_REGISTRY environment variable set"
        echo "💡 Multi-arch images need to be pushed to a registry"
        echo "🔄 Building for current platform only..."

        docker buildx build \
            --platform "$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')" \
            --file "$DOCKERFILE" \
            --tag "$IMAGE_NAME:$TAG" \
            --load \
            $PROGRESS_FLAG \
            ../

        echo "✅ Single-architecture image built for current platform"
        echo ""
        echo "📋 To build for multiple architectures:"
        echo "  DOCKER_REGISTRY=your-registry.com ./build.sh"
    fi
fi

echo ""
echo "📋 Usage examples:"
echo ""
echo "🔑 Nintendo Switch Keys Setup:"
echo "  NSZ requires prod.keys file. Use docker volumes to mount your keys:"
echo ""
echo "  # Direct docker usage:"
echo "  docker run --rm -v \"\$(pwd)\":/data $IMAGE_NAME:$TAG --help"
echo "  docker run --rm -v \"\$(pwd)\":/data -v \"\$HOME/.switch/prod.keys\":/root/.switch/prod.keys $IMAGE_NAME:$TAG game.nsp"
echo "  docker run --rm -v \"\$(pwd)\":/data -v \"\$HOME/.switch/prod.keys\":/usr/local/bin/keys.txt $IMAGE_NAME:$TAG -D game.nsz"
echo ""
echo "🔧 Build options:"
echo "  # Build for current platform only:"
echo "  ./build.sh --single-arch"
echo ""
echo "  # Build with verbose output:"
echo "  ./build.sh --verbose"
echo "  VERBOSE=true ./build.sh"
echo ""
echo "  # Build and push multi-arch to registry:"
echo "  DOCKER_REGISTRY=your-registry.com ./build.sh"
echo ""
echo "🔧 Create a shell function for easier usage:"
echo "  # Add to your ~/.bashrc or ~/.zshrc:"
echo "  nsz() {"
echo "      docker run --rm -v \"\$(pwd)\":/data -v \"\$HOME/.switch/prod.keys\":/root/.switch/prod.keys $IMAGE_NAME:$TAG \"\$@\""
echo "  }"
echo ""
echo "  # Then use like a normal command:"
echo "  nsz game.nsp"
echo "  nsz -D game.nsz"
echo "  nsz --help"
echo ""
echo "🎯 Image is ready to use!"