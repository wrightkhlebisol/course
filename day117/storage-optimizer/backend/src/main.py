from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
from storage.optimizer import StorageOptimizer
from policy.engine import PolicyEngine
from analytics.cost import CostAnalyzer
from api.routes import router

app = FastAPI(title="Storage Optimization System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
storage_optimizer = StorageOptimizer()
policy_engine = PolicyEngine()
cost_analyzer = CostAnalyzer()

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    await storage_optimizer.initialize()
    await policy_engine.start()
    await cost_analyzer.start_monitoring()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            metrics = await cost_analyzer.get_real_time_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
