#!/bin/bash
# Build and push Docker image for Raspberry Pi

IMAGE_NAME="sensor-hub"
VERSION=${1:-latest}
REGISTRY=${REGISTRY:-"localhost:5000"}  # Adjust to your registry

echo "Building Docker image for ARM64 (Raspberry Pi 5)..."

# Build for ARM64 architecture
docker buildx build \
    --platform linux/arm64 \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:latest \
    .

echo "Image built: ${IMAGE_NAME}:${VERSION}"

# Optionally push to registry
if [ "$PUSH" = "true" ]; then
    echo "Pushing to registry ${REGISTRY}..."
    docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:${VERSION}
    docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}
    echo "Pushed to ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
fi

echo "Done!"
echo ""
echo "To deploy to Kubernetes:"
echo "  kubectl apply -f k8s-deployment.yaml"
echo ""
echo "To push to registry:"
echo "  PUSH=true REGISTRY=your-registry.com ./build-docker.sh"
