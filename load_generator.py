#!/usr/bin/env python3
"""
Load generator for testing ML service under load and triggering alerts
"""

import grpc
import time
import random
import argparse
from concurrent.futures import ThreadPoolExecutor
from generated import model_pb2, model_pb2_grpc

def make_request(port, add_delay=False, cause_error=False):
    """Make a single request to the ML service"""
    try:
        channel = grpc.insecure_channel(f'localhost:{port}')
        stub = model_pb2_grpc.PredictionServiceStub(channel)
        
        if cause_error:
            features = []
        else:
            features = [
                random.uniform(4.0, 8.0),
                random.uniform(2.0, 4.5),
                random.uniform(1.0, 7.0),
                random.uniform(0.1, 2.5)
            ]
        
        if add_delay:
            time.sleep(random.uniform(0.5, 2.0))
        
        response = stub.Predict(model_pb2.PredictRequest(features=features))
        return True, response.prediction
    except Exception as e:
        return False, str(e)


def generate_load(port=50051, duration=60, rps=10, error_rate=0, add_delay=False):
    """Generate load on the ML service"""
    print(f"Starting load generator:")
    print(f"  Port: {port}")
    print(f"  Duration: {duration}s")
    print(f"  Target RPS: {rps}")
    print(f"  Error rate: {error_rate}%")
    print(f"  Add delay: {add_delay}")
    print()
    
    start_time = time.time()
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    
    with ThreadPoolExecutor(max_workers=rps) as executor:
        while time.time() - start_time < duration:
            batch_start = time.time()
            
            futures = []
            for _ in range(rps):
                cause_error = random.random() < (error_rate / 100)
                future = executor.submit(make_request, port, add_delay, cause_error)
                futures.append(future)
            
            for future in futures:
                success, result = future.result()
                total_requests += 1
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if total_requests % 10 == 0:
                current_error_rate = (failed_requests / total_requests) * 100
                print(f"[{int(time.time() - start_time)}s] "
                      f"Total: {total_requests}, "
                      f"Success: {successful_requests}, "
                      f"Failed: {failed_requests} "
                      f"({current_error_rate:.1f}%)")
    
    print()
    print("Load generation completed!")
    print(f"Total requests: {total_requests}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {failed_requests}")
    print(f"Error rate: {(failed_requests / total_requests) * 100:.2f}%")


def main():
    parser = argparse.ArgumentParser(description='Load generator for ML service')
    parser.add_argument('--port', type=int, default=50051, help='Service port')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')
    parser.add_argument('--rps', type=int, default=10, help='Requests per second')
    parser.add_argument('--error-rate', type=int, default=0, help='Error rate percentage (0-100)')
    parser.add_argument('--add-delay', action='store_true', help='Add artificial delay to trigger latency alerts')
    
    args = parser.parse_args()
    
    generate_load(
        port=args.port,
        duration=args.duration,
        rps=args.rps,
        error_rate=args.error_rate,
        add_delay=args.add_delay
    )


if __name__ == '__main__':
    main()
