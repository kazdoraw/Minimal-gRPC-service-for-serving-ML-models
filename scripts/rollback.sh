#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_DIR="$PROJECT_DIR/nginx"

echo "=== Blue-Green Deployment Rollback ==="
echo ""

BACKUP_CONFIG="$NGINX_DIR/nginx.conf.backup"

if [ ! -f "$BACKUP_CONFIG" ]; then
    echo "❌ No backup configuration found!"
    echo "Cannot rollback without backup."
    exit 1
fi

CURRENT_CONFIG="$NGINX_DIR/nginx.conf"

if grep -q "ml-service-blue:50051" "$CURRENT_CONFIG" && ! grep -q "# server ml-service-blue:50051" "$CURRENT_CONFIG"; then
    CURRENT="blue"
else
    CURRENT="green"
fi

echo "Current active: $CURRENT"
echo ""

echo "Step 1: Restoring previous configuration..."
cp "$BACKUP_CONFIG" "$CURRENT_CONFIG"
echo "✅ Configuration restored"
echo ""

echo "Step 2: Testing Nginx configuration..."
docker exec ml-nginx-lb nginx -t
echo "✅ Configuration valid"
echo ""

echo "Step 3: Reloading Nginx..."
docker exec ml-nginx-lb nginx -s reload
echo "✅ Nginx reloaded"
echo ""

echo "Step 4: Verifying rollback..."
sleep 2

VERIFY=$(cd "$PROJECT_DIR" && /opt/anaconda3/envs/ml-python312/bin/python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
try:
    channel = grpc.insecure_channel('localhost:50050')
    stub = model_pb2_grpc.PredictionServiceStub(channel)
    response = stub.Health(model_pb2.HealthRequest())
    print(f'Version: {response.model_version}, Status: {response.status}')
except Exception as e:
    print('error')
")

if [ "$VERIFY" != "error" ]; then
    echo "✅ Rollback successful!"
    echo ""
    echo "$VERIFY"
    echo ""
    echo "System restored to previous state"
else
    echo "❌ Verification failed after rollback!"
    exit 1
fi
