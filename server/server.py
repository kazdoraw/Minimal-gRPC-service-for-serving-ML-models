"""
gRPC server implementation for ML model predictions.
Provides Health and Predict endpoints.
"""

import os
import sys
import pickle
import logging
from concurrent import futures

import grpc
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated import model_pb2
from generated import model_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionServicer(model_pb2_grpc.PredictionServiceServicer):
    """Implementation of PredictionService"""
    
    def __init__(self):
        """Initialize servicer and load ML model"""
        self.model_version = os.getenv('MODEL_VERSION', 'v1.0.0')
        self.model_path = os.getenv('MODEL_PATH', 'models/model.pkl')
        self.model = self._load_model()
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
        try:
            response = model_pb2.HealthResponse(
                status="ok",
                model_version=self.model_version
            )
            logger.info("Health check successful")
            return response
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Health check failed: {str(e)}")
            return model_pb2.HealthResponse()
    
    def Predict(self, request, context):
        """Prediction endpoint"""
        try:
            if not request.features:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Features array is empty")
                return model_pb2.PredictResponse()
            
            features = np.array(request.features).reshape(1, -1)
            logger.info(f"Received prediction request with {len(request.features)} features")
            
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            confidence = float(max(probabilities))
            
            response = model_pb2.PredictResponse(
                prediction=str(prediction),
                confidence=confidence,
                model_version=self.model_version
            )
            
            logger.info(f"Prediction successful: class={prediction}, confidence={confidence:.4f}")
            return response
            
        except ValueError as e:
            logger.error(f"Invalid input data: {str(e)}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid input data: {str(e)}")
            return model_pb2.PredictResponse()
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Prediction failed: {str(e)}")
            return model_pb2.PredictResponse()


def serve():
    """Start gRPC server"""
    port = os.getenv('PORT', '50051')
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(
        PredictionServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"Server started on port {port}")
    logger.info(f"Model version: {os.getenv('MODEL_VERSION', 'v1.0.0')}")
    logger.info(f"Model path: {os.getenv('MODEL_PATH', 'models/model.pkl')}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop(0)


if __name__ == '__main__':
    serve()
