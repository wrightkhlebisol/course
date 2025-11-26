"""Real-time inference service"""
import numpy as np
from pathlib import Path
from src.feature_engineering.log_features import LogFeatureExtractor
from src.models.anomaly_detection import AnomalyDetectionModel
from src.models.failure_prediction import FailurePredictionModel
from typing import Dict, List

class LogPredictor:
    """Serve predictions from trained models"""
    
    def __init__(self, models_dir: str = "data/models"):
        self.feature_extractor = LogFeatureExtractor()
        
        # Load anomaly detector
        self.anomaly_model = AnomalyDetectionModel(input_dim=50)  # Will be updated on load
        anomaly_path = Path(models_dir) / "anomaly_detection"
        if anomaly_path.exists():
            self.anomaly_model.load(str(anomaly_path))
        
        # Load failure predictor
        self.failure_model = FailurePredictionModel(input_dim=50)
        failure_path = Path(models_dir) / "failure_prediction"
        if failure_path.exists():
            self.failure_model.load(str(failure_path))
        
        self.prediction_cache = {}
        
    def predict_anomaly(self, log_entry: Dict) -> Dict:
        """Predict if log is anomalous"""
        features = self.feature_extractor.extract_all_features(log_entry)
        features = features.reshape(1, -1)
        
        is_anomaly, confidence = self.anomaly_model.predict_anomaly(features)
        
        return {
            'is_anomaly': bool(is_anomaly[0]),
            'confidence': float(confidence[0]),
            'model': 'anomaly_detection'
        }
    
    def predict_failure(self, log_sequence: List[Dict]) -> Dict:
        """Predict failure probability from log sequence"""
        features = self.feature_extractor.extract_batch(log_sequence)
        
        # Pad or truncate to sequence length
        seq_len = self.failure_model.sequence_length
        if len(features) < seq_len:
            padding = np.zeros((seq_len - len(features), features.shape[1]))
            features = np.vstack([padding, features])
        else:
            features = features[-seq_len:]
        
        features = features.reshape(1, seq_len, -1)
        failure_prob = self.failure_model.predict_failure(features)
        
        return {
            'failure_probability': float(failure_prob[0]),
            'time_horizon_minutes': 30,
            'model': 'failure_prediction'
        }
    
    def predict_batch(self, log_entries: List[Dict]) -> List[Dict]:
        """Batch prediction for efficiency"""
        features = self.feature_extractor.extract_batch(log_entries)
        is_anomaly, confidence = self.anomaly_model.predict_anomaly(features)
        
        results = []
        for i, log in enumerate(log_entries):
            results.append({
                'log_id': log.get('id', f'log_{i}'),
                'is_anomaly': bool(is_anomaly[i]),
                'confidence': float(confidence[i]),
                'timestamp': log.get('timestamp')
            })
        
        return results
