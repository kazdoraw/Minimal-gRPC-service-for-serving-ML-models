#!/usr/bin/env python3
"""
Train v1.1.0 model with different parameters
"""

import pickle
from pathlib import Path
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import numpy as np

def train_and_save_model_v2():
    """Train and save model v1.1.0 with different parameters"""
    
    print("Loading Iris dataset...")
    iris = load_iris()
    X, y = iris.data, iris.target
    
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("Training LogisticRegression model v1.1.0...")
    print("Parameters: max_iter=300, C=1.5, solver='lbfgs'")
    
    model = LogisticRegression(max_iter=300, C=1.5, solver='lbfgs', random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {accuracy:.2%}")
    
    models_dir = Path("models/v1.1.0")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "model.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model v1.1.0 saved to {model_path}")
    print(f"File size: {model_path.stat().st_size} bytes")
    
    print("\nTest prediction:")
    test_sample = X_test[0].reshape(1, -1)
    prediction = model.predict(test_sample)[0]
    proba = model.predict_proba(test_sample)[0]
    confidence = float(max(proba))
    
    print(f"  Input: {test_sample[0]}")
    print(f"  Prediction: class {prediction} ({iris.target_names[prediction]})")
    print(f"  Confidence: {confidence:.4f}")
    print(f"  Probabilities: {proba}")

if __name__ == "__main__":
    train_and_save_model_v2()
