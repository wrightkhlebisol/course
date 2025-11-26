"""Autoencoder for anomaly detection"""
import tensorflow as tf
import numpy as np
from typing import Tuple

class AnomalyDetectionModel:
    """Autoencoder-based anomaly detector"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.model = self._build_model()
        self.threshold = None
        
    def _build_model(self) -> tf.keras.Model:
        """Build autoencoder architecture"""
        # Encoder
        encoder_input = tf.keras.Input(shape=(self.input_dim,))
        encoded = tf.keras.layers.Dense(128, activation='relu')(encoder_input)
        encoded = tf.keras.layers.BatchNormalization()(encoded)
        encoded = tf.keras.layers.Dropout(0.2)(encoded)
        encoded = tf.keras.layers.Dense(64, activation='relu')(encoded)
        encoded = tf.keras.layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = tf.keras.layers.Dense(64, activation='relu')(encoded)
        decoded = tf.keras.layers.BatchNormalization()(decoded)
        decoded = tf.keras.layers.Dropout(0.2)(decoded)
        decoded = tf.keras.layers.Dense(128, activation='relu')(decoded)
        decoded = tf.keras.layers.Dense(self.input_dim, activation='sigmoid')(decoded)
        
        # Full autoencoder
        autoencoder = tf.keras.Model(encoder_input, decoded)
        autoencoder.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        return autoencoder
    
    def train(self, X_train: np.ndarray, X_val: np.ndarray, 
              epochs: int = 50, batch_size: int = 32) -> tf.keras.callbacks.History:
        """Train autoencoder on normal log patterns"""
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=5, restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6
            )
        ]
        
        history = self.model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, X_val),
            callbacks=callbacks,
            verbose=1
        )
        
        # Calculate reconstruction error threshold
        reconstructed = self.model.predict(X_val, verbose=0)
        reconstruction_errors = np.mean(np.square(X_val - reconstructed), axis=1)
        self.threshold = np.percentile(reconstruction_errors, 95)
        
        return history
    
    def predict_anomaly(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies with confidence scores"""
        reconstructed = self.model.predict(X, verbose=0)
        reconstruction_errors = np.mean(np.square(X - reconstructed), axis=1)
        
        is_anomaly = reconstruction_errors > self.threshold
        confidence_scores = np.clip(reconstruction_errors / (self.threshold + 1e-7), 0, 1)
        
        return is_anomaly, confidence_scores
    
    def save(self, path: str) -> None:
        """Save model and threshold"""
        self.model.save(f"{path}/autoencoder.keras")
        np.save(f"{path}/threshold.npy", self.threshold)
    
    def load(self, path: str) -> None:
        """Load model and threshold"""
        self.model = tf.keras.models.load_model(f"{path}/autoencoder.keras")
        self.threshold = np.load(f"{path}/threshold.npy")
