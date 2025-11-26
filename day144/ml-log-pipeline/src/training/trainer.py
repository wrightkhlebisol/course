"""Model training orchestration"""
import yaml
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from src.feature_engineering.log_features import LogFeatureExtractor
from src.models.anomaly_detection import AnomalyDetectionModel
from src.models.failure_prediction import FailurePredictionModel
import json

class ModelTrainer:
    """Orchestrate model training"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)['ml_pipeline']
        
        self.feature_extractor = LogFeatureExtractor(
            self.config['feature_engineering']['window_size_minutes']
        )
        
    def load_training_data(self, data_path: str = "data/processed/training_logs.json"):
        """Load and prepare training data"""
        with open(data_path) as f:
            logs = json.load(f)
        
        # Extract features
        features = self.feature_extractor.extract_batch(logs)
        
        # Extract labels (if available)
        labels = np.array([log.get('is_failure', 0) for log in logs])
        
        return features, labels
    
    def train_anomaly_detector(self, features: np.ndarray, save_path: str):
        """Train anomaly detection model"""
        print("\n🔍 Training Anomaly Detection Model...")
        
        # Use only normal logs for training
        normal_features = features  # Assumes pre-filtered normal data
        
        X_train, X_val = train_test_split(normal_features, test_size=0.2, random_state=42)
        
        model = AnomalyDetectionModel(
            input_dim=X_train.shape[1],
            encoding_dim=self.config['models']['anomaly_detection']['encoding_dim']
        )
        
        history = model.train(
            X_train, X_val,
            epochs=self.config['training']['epochs'],
            batch_size=self.config['training']['batch_size']
        )
        
        # Save model
        Path(save_path).mkdir(parents=True, exist_ok=True)
        model.save(save_path)
        
        print(f"✅ Anomaly detector saved to {save_path}")
        print(f"   Final validation loss: {history.history['val_loss'][-1]:.4f}")
        
        return model, history
    
    def train_failure_predictor(self, features: np.ndarray, labels: np.ndarray, save_path: str):
        """Train failure prediction model"""
        print("\n⚠️  Training Failure Prediction Model...")
        
        model = FailurePredictionModel(
            input_dim=features.shape[1],
            sequence_length=self.config['models']['failure_prediction']['sequence_length'],
            hidden_units=self.config['models']['failure_prediction']['hidden_units']
        )
        
        # Prepare sequences
        X, y = model.prepare_sequences(features, labels)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        history = model.train(
            X_train, y_train, X_val, y_val,
            epochs=self.config['training']['epochs'],
            batch_size=self.config['training']['batch_size']
        )
        
        # Save model
        Path(save_path).mkdir(parents=True, exist_ok=True)
        model.save(save_path)
        
        print(f"✅ Failure predictor saved to {save_path}")
        print(f"   Final validation AUC: {history.history['val_auc'][-1]:.4f}")
        
        return model, history
    
    def train_all_models(self, data_path: str, models_dir: str = "data/models"):
        """Train all models"""
        features, labels = self.load_training_data(data_path)
        
        # Train anomaly detector
        anomaly_model, _ = self.train_anomaly_detector(
            features, 
            f"{models_dir}/anomaly_detection"
        )
        
        # Train failure predictor
        failure_model, _ = self.train_failure_predictor(
            features, 
            labels,
            f"{models_dir}/failure_prediction"
        )
        
        print("\n🎉 All models trained successfully!")
        
        return anomaly_model, failure_model
