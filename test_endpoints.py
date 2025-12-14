#!/usr/bin/env python3
"""Manual testing of gRPC endpoints"""

import grpc
from generated import model_pb2, model_pb2_grpc

# Connect to server
channel = grpc.insecure_channel('localhost:50051')
stub = model_pb2_grpc.PredictionServiceStub(channel)

# Test Health endpoint
print("Testing /health endpoint:")
health_request = model_pb2.HealthRequest()
health_response = stub.Health(health_request)
print(f"  Status: {health_response.status}")
print(f"  Model Version: {health_response.model_version}\n")

# Test Predict endpoint
print("Testing /predict endpoint:")
predict_request = model_pb2.PredictRequest(features=[5.1, 3.5, 1.4, 0.2])
predict_response = stub.Predict(predict_request)
print(f"  Prediction: {predict_response.prediction}")
print(f"  Confidence: {predict_response.confidence:.4f}")
print(f"  Model Version: {predict_response.model_version}")
