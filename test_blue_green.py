#!/usr/bin/env python3
"""
Comprehensive Blue-Green deployment test script
Creates detailed test report with all endpoints
"""

import grpc
from generated import model_pb2, model_pb2_grpc
import sys

def test_endpoint(port, name):
    """Test health and predict endpoints"""
    print(f"\n{'='*60}")
    print(f"Testing {name} on port {port}")
    print('='*60)
    
    try:
        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = model_pb2_grpc.PredictionServiceStub(channel)
        
        print("\n1. Health Check:")
        print("-" * 40)
        health_response = stub.Health(model_pb2.HealthRequest())
        print(f"   Status:        {health_response.status}")
        print(f"   Model Version: {health_response.model_version}")
        
        print("\n2. Prediction Test:")
        print("-" * 40)
        test_features = [5.1, 3.5, 1.4, 0.2]
        print(f"   Input:         {test_features}")
        
        predict_response = stub.Predict(model_pb2.PredictRequest(features=test_features))
        print(f"   Prediction:    {predict_response.prediction}")
        print(f"   Confidence:    {predict_response.confidence:.4f}")
        print(f"   Model Version: {predict_response.model_version}")
        
        print("\n3. Multiple predictions:")
        print("-" * 40)
        test_cases = [
            [5.1, 3.5, 1.4, 0.2],  # setosa
            [6.3, 2.5, 4.9, 1.5],  # versicolor
            [6.5, 3.0, 5.8, 2.2],  # virginica
        ]
        
        for features in test_cases:
            response = stub.Predict(model_pb2.PredictRequest(features=features))
            print(f"   {features} → class {response.prediction} (conf: {response.confidence:.4f})")
        
        print(f"\n✅ {name} is healthy and operational!")
        return True
        
    except Exception as e:
        print(f"\n❌ {name} failed: {str(e)}")
        return False

def main():
    print("="*60)
    print("Blue-Green Deployment Test Suite")
    print("="*60)
    
    results = []
    
    results.append(("Nginx (Active)", test_endpoint(50050, "Nginx Load Balancer (Active)")))
    
    print("\n\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}: {'PASS' if status else 'FAIL'}")
    
    all_passed = all(status for _, status in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Blue-Green deployment is operational.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
