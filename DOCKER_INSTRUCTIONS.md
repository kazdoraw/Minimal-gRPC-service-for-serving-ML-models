# Docker Build and Run Instructions

## Prerequisites
- Docker Desktop installed and running

## Build Docker Image

```bash
cd /Users/Shared/ml/DEPLOY/HW2
docker build -t grpc-ml-service .
```

## Run Docker Container

```bash
docker run -p 50051:50051 grpc-ml-service
```

## Test with Python Client

In a new terminal:

```bash
cd /Users/Shared/ml/DEPLOY/HW2
python -m client.client
```

## Test with grpcurl (optional)

```bash
grpcurl -plaintext localhost:50051 mlservice.v1.PredictionService/Health
```

Expected output:
```json
{
  "status": "ok",
  "modelVersion": "v1.0.0"
}
```

## Stop Container

```bash
docker ps
docker stop <container_id>
```

## Environment Variables

The container uses the following environment variables:
- `PORT=50051`
- `MODEL_PATH=/app/models/model.pkl`
- `MODEL_VERSION=v1.0.0`

Override them when running:
```bash
docker run -p 50051:50051 \
  -e MODEL_VERSION=v2.0.0 \
  grpc-ml-service
```
