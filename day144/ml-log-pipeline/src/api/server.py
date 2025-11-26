"""FastAPI inference API"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.inference.predictor import LogPredictor
import uvicorn

app = FastAPI(title="ML Log Pipeline API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
predictor = LogPredictor()

class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    component: str
    message: str
    metrics: Optional[Dict] = {}

class PredictionResponse(BaseModel):
    is_anomaly: bool
    confidence: float
    model: str

@app.post("/predict/anomaly", response_model=PredictionResponse)
async def predict_anomaly(log: LogEntry):
    """Predict if log entry is anomalous"""
    try:
        result = predictor.predict_anomaly(log.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/failure")
async def predict_failure(logs: List[LogEntry]):
    """Predict failure probability from log sequence"""
    try:
        log_dicts = [log.dict() for log in logs]
        result = predictor.predict_failure(log_dicts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
async def predict_batch(logs: List[LogEntry]):
    """Batch anomaly prediction"""
    try:
        log_dicts = [log.dict() for log in logs]
        results = predictor.predict_batch(log_dicts)
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "models_loaded": True}

@app.get("/metrics")
async def get_metrics():
    """Model performance metrics"""
    return {
        "anomaly_detector": {
            "threshold": float(predictor.anomaly_model.threshold) if predictor.anomaly_model.threshold else None
        },
        "requests_processed": 0  # Placeholder
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
