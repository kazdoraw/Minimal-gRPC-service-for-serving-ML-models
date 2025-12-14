#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_DIR="$PROJECT_DIR/nginx"

echo "=== Blue-Green Deployment Switch ==="
echo ""

CURRENT_CONFIG="$NGINX_DIR/nginx.conf"

if grep -q "ml-service-blue:50051" "$CURRENT_CONFIG" && ! grep -q "# server ml-service-blue:50051" "$CURRENT_CONFIG"; then
    CURRENT="blue"
    TARGET="green"
    TARGET_VERSION="v1.1.0"
else
    CURRENT="green"
    TARGET="blue"
    TARGET_VERSION="v1.0.0"
fi

echo "Current active: $CURRENT"
echo "Switching to: $TARGET ($TARGET_VERSION)"
echo ""

echo "Step 1: Health check for $TARGET..."
if [ "$TARGET" = "blue" ]; then
    TARGET_PORT=50051
else
    TARGET_PORT=50051
fi

HEALTH_CHECK=$(docker exec ml-service-$TARGET python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
try:
    channel = grpc.insecure_channel('localhost:$TARGET_PORT')
    stub = model_pb2_grpc.PredictionServiceStub(channel)
    response = stub.Health(model_pb2.HealthRequest())
    print(response.status)
except Exception as e:
    print('error')
" 2>/dev/null)

if [ "$HEALTH_CHECK" != "ok" ]; then
    echo "❌ Health check failed for $TARGET! Aborting switch."
    exit 1
fi

echo "✅ Health check passed for $TARGET"
echo ""

echo "Step 2: Backing up current Nginx config..."
cp "$CURRENT_CONFIG" "$NGINX_DIR/nginx.conf.backup"
echo "✅ Backup created"
echo ""

echo "Step 3: Switching Nginx configuration to $TARGET..."
if [ "$TARGET" = "green" ]; then
    cp "$NGINX_DIR/nginx-green.conf" "$CURRENT_CONFIG"
else
    sed -i.tmp 's/server ml-service-green:50051;/# server ml-service-green:50051;/' "$CURRENT_CONFIG"
    sed -i.tmp 's/# server ml-service-blue:50051;/server ml-service-blue:50051;/' "$CURRENT_CONFIG"
    rm -f "$CURRENT_CONFIG.tmp"
fi
echo "✅ Configuration updated"
echo ""

echo "Step 4: Reloading Nginx..."
docker exec ml-nginx-lb nginx -t
docker exec ml-nginx-lb nginx -s reload
echo "✅ Nginx reloaded"
echo ""

echo "Step 5: Verifying switch..."
sleep 2

VERIFY=$(cd "$PROJECT_DIR" && /opt/anaconda3/envs/ml-python312/bin/python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
try:
    channel = grpc.insecure_channel('localhost:50050')
    stub = model_pb2_grpc.PredictionServiceStub(channel)
    response = stub.Health(model_pb2.HealthRequest())
    print(response.model_version)
except Exception as e:
    print('error')
")

if [ "$VERIFY" = "$TARGET_VERSION" ]; then
    echo "✅ Switch successful!"
    echo ""
    echo "Active version: $TARGET_VERSION"
    echo "Traffic is now routed to: $TARGET"
    echo ""
    echo "To rollback, run: ./scripts/rollback.sh"
else
    echo "❌ Verification failed! Rolling back..."
    cp "$NGINX_DIR/nginx.conf.backup" "$CURRENT_CONFIG"
    docker exec ml-nginx-lb nginx -s reload
    echo "Rollback completed"
    exit 1
fi
