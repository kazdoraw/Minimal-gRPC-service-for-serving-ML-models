"""
gRPC server implementation for ML model predictions.
Provides Health and Predict endpoints.
"""

import os
import sys
import pickle
import logging
import time
from concurrent import futures
from http.server import HTTPServer, BaseHTTPRequestHandler

import grpc
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import model_pb2
from generated import model_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['method'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
)

REQUEST_COUNT = Counter(
    'request_total',
    'Total number of requests',
    ['method', 'status']
)

ERROR_COUNT = Counter(
    'request_errors_total',
    'Total number of errors',
    ['method', 'error_type']
)

MODEL_INFERENCE_TIME = Histogram(
    'model_prediction_duration_seconds',
    'Model inference time in seconds',
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

MODEL_INFO = Gauge(
    'model_info',
    'Model information',
    ['version', 'path']
)


class PredictionServicer(model_pb2_grpc.PredictionServiceServicer):
    """Implementation of PredictionService"""
    
    def __init__(self):
        """Initialize servicer and load ML model"""
        self.model_version = os.getenv('MODEL_VERSION', 'v1.0.0')
        self.model_path = os.getenv('MODEL_PATH', 'models/model.pkl')
        self.model = self._load_model()
        MODEL_INFO.labels(version=self.model_version, path=self.model_path).set(1)
        logger.info(f"PredictionServicer initialized with model version {self.model_version}")
    
    def _load_model(self):
        """Load ML model from pickle file"""
        try:
            with open(self.model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Model loaded successfully from {self.model_path}")
            return model
        except FileNotFoundError:
            logger.error(f"Model file not found: {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def Health(self, request, context):
        """Health check endpoint"""
        start_time = time.time()
        try:
            response = model_pb2.HealthResponse(
                status="ok",
                model_version=self.model_version
            )
            REQUEST_COUNT.labels(method='Health', status='success').inc()
            logger.info("Health check successful")
            return response
        except Exception as e:
            ERROR_COUNT.labels(method='Health', error_type=type(e).__name__).inc()
            REQUEST_COUNT.labels(method='Health', status='error').inc()
            logger.error(f"Health check failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Health check failed: {str(e)}")
            return model_pb2.HealthResponse()
        finally:
            REQUEST_LATENCY.labels(method='Health').observe(time.time() - start_time)
    
    def Predict(self, request, context):
        """Prediction endpoint"""
        start_time = time.time()
        try:
            if not request.features:
                ERROR_COUNT.labels(method='Predict', error_type='EmptyFeatures').inc()
                REQUEST_COUNT.labels(method='Predict', status='error').inc()
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Features array is empty")
                return model_pb2.PredictResponse()
            
            features = np.array(request.features).reshape(1, -1)
            logger.info(f"Received prediction request with {len(request.features)} features")
            
            inference_start = time.time()
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            MODEL_INFERENCE_TIME.observe(time.time() - inference_start)
            
            confidence = float(max(probabilities))
            
            response = model_pb2.PredictResponse(
                prediction=str(prediction),
                confidence=confidence,
                model_version=self.model_version
            )
            
            REQUEST_COUNT.labels(method='Predict', status='success').inc()
            logger.info(f"Prediction successful: class={prediction}, confidence={confidence:.4f}")
            return response
            
        except ValueError as e:
            ERROR_COUNT.labels(method='Predict', error_type='ValueError').inc()
            REQUEST_COUNT.labels(method='Predict', status='error').inc()
            logger.error(f"Invalid input data: {str(e)}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid input data: {str(e)}")
            return model_pb2.PredictResponse()
        except Exception as e:
            ERROR_COUNT.labels(method='Predict', error_type=type(e).__name__).inc()
            REQUEST_COUNT.labels(method='Predict', status='error').inc()
            logger.error(f"Prediction failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Prediction failed: {str(e)}")
            return model_pb2.PredictResponse()
        finally:
            REQUEST_LATENCY.labels(method='Predict').observe(time.time() - start_time)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def start_metrics_server(port=8000):
    """Start HTTP server for Prometheus metrics"""
    metrics_server = HTTPServer(('', port), MetricsHandler)
    logger.info(f"Metrics server started on port {port}")
    metrics_server.serve_forever()


def serve():
    """Start gRPC server and metrics server"""
    grpc_port = os.getenv('PORT', '50051')
    metrics_port = int(os.getenv('METRICS_PORT', '8000'))
    
    import threading
    metrics_thread = threading.Thread(target=start_metrics_server, args=(metrics_port,), daemon=True)
    metrics_thread.start()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(
        PredictionServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{grpc_port}')
    server.start()
    
    logger.info(f"gRPC server started on port {grpc_port}")
    logger.info(f"Metrics endpoint: http://localhost:{metrics_port}/metrics")
    logger.info(f"Model version: {os.getenv('MODEL_VERSION', 'v1.0.0')}")
    logger.info(f"Model path: {os.getenv('MODEL_PATH', 'models/model.pkl')}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop(0)


if __name__ == '__main__':
    serve()
