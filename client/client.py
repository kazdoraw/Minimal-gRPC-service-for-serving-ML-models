"""
gRPC client for testing PredictionService.
Tests both Health and Predict endpoints.
"""

import sys
import os
import grpc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import model_pb2
from generated import model_pb2_grpc


def test_health(stub):
    """Test Health endpoint"""
    print("\n" + "="*50)
    print("Testing Health endpoint")
    print("="*50)
    
    try:
        request = model_pb2.HealthRequest()
        response = stub.Health(request, timeout=5.0)
        
        print(f"Status: {response.status}")
        print(f"Model Version: {response.model_version}")
        print("Health check: OK")
        return True
        
    except grpc.RpcError as e:
        print(f"Health check failed: {e.code()}")
        print(f"Details: {e.details()}")
        return False


def test_predict(stub):
    """Test Predict endpoint"""
    print("\n" + "="*50)
    print("Testing Predict endpoint")
    print("="*50)
    
    try:
        test_features = [5.1, 3.5, 1.4, 0.2]
        print(f"Input features: {test_features}")
        
        request = model_pb2.PredictRequest(features=test_features)
        response = stub.Predict(request, timeout=5.0)
        
        print(f"Prediction: {response.prediction}")
        print(f"Confidence: {response.confidence:.4f}")
        print(f"Model Version: {response.model_version}")
        print("Prediction: OK")
        return True
        
    except grpc.RpcError as e:
        print(f"Prediction failed: {e.code()}")
        print(f"Details: {e.details()}")
        return False


def run():
    """Run all tests"""
    server_address = 'localhost:50051'
    
    print(f"Connecting to server at {server_address}...")
    
    with grpc.insecure_channel(server_address) as channel:
        stub = model_pb2_grpc.PredictionServiceStub(channel)
        
        health_ok = test_health(stub)
        predict_ok = test_predict(stub)
        
        print("\n" + "="*50)
        print("Test Results")
        print("="*50)
        print(f"Health check: {'PASS' if health_ok else 'FAIL'}")
        print(f"Predict test: {'PASS' if predict_ok else 'FAIL'}")
        print(f"Overall: {'ALL TESTS PASSED' if (health_ok and predict_ok) else 'SOME TESTS FAILED'}")
        print("="*50)


if __name__ == '__main__':
    run()
