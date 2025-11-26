"""LSTM for failure prediction"""
import tensorflow as tf
import numpy as np
from typing import Tuple

class FailurePredictionModel:
    """LSTM-based failure predictor"""
    
    def __init__(self, input_dim: int, sequence_length: int = 60, hidden_units: int = 128):
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.hidden_units = hidden_units
        self.model = self._build_model()
        
    def _build_model(self) -> tf.keras.Model:
        """Build LSTM architecture"""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(
                self.hidden_units, 
                return_sequences=True,
                input_shape=(self.sequence_length, self.input_dim)
            ),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.LSTM(64, return_sequences=False),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')  # Failure probability
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def prepare_sequences(self, features: np.ndarray, labels: np.ndarray = None) -> Tuple:
        """Prepare sequential data for LSTM"""
        sequences = []
        if labels is not None:
            sequence_labels = []
        
        for i in range(len(features) - self.sequence_length):
            sequences.append(features[i:i + self.sequence_length])
            if labels is not None:
                sequence_labels.append(labels[i + self.sequence_length])
        
        X = np.array(sequences)
        y = np.array(sequence_labels) if labels is not None else None
        
        return (X, y) if y is not None else X
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 50, batch_size: int = 32) -> tf.keras.callbacks.History:
        """Train failure prediction model"""
        # Handle class imbalance
        neg_count = np.sum(y_train == 0)
        pos_count = np.sum(y_train == 1)
        class_weight = {0: 1.0, 1: neg_count / pos_count if pos_count > 0 else 1.0}
        
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_auc', mode='max', patience=5, restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6
            )
        ]
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=callbacks,
            class_weight=class_weight,
            verbose=1
        )
        
        return history
    
    def predict_failure(self, X: np.ndarray) -> np.ndarray:
        """Predict failure probability"""
        return self.model.predict(X, verbose=0).flatten()
    
    def save(self, path: str) -> None:
        """Save model"""
        self.model.save(f"{path}/failure_predictor.keras")
    
    def load(self, path: str) -> None:
        """Load model"""
        self.model = tf.keras.models.load_model(f"{path}/failure_predictor.keras")
