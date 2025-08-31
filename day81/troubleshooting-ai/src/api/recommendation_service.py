"""
FastAPI service for incident recommendations
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import json
import numpy as np

from core.incident import Incident, Solution, Recommendation
from ml.similarity_engine import SimilarityEngine

# Pydantic models for API
class IncidentRequest(BaseModel):
    title: str
    description: str
    error_type: str
    affected_service: str
    severity: str
    environment: str
    logs: List[str] = []
    metrics: Dict[str, float] = {}

class FeedbackRequest(BaseModel):
    incident_id: str
    solution_id: str
    was_helpful: bool
    resolution_time: Optional[int] = None
    comments: Optional[str] = None

class ExecuteRequest(BaseModel):
    solution_id: str
    incident_id: str
    environment: str = "production"

class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    steps_executed: List[Dict]
    execution_time_ms: int
    success: bool
    logs: List[str]

class RecommendationResponse(BaseModel):
    recommendations: List[Dict]
    processing_time_ms: int
    similar_incidents_count: int

# Initialize FastAPI app
app = FastAPI(title="Troubleshooting Recommendation API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML engine
similarity_engine = SimilarityEngine()

@app.on_event("startup")
async def startup_event():
    """Load historical data and train model"""
    await load_sample_data()

async def load_sample_data():
    """Load sample incidents and solutions for demonstration"""
    
    # Sample incidents
    sample_incidents = [
        {
            "id": "inc_001",
            "title": "Database Connection Timeout",
            "description": "Application cannot connect to PostgreSQL database, timeout after 30 seconds",
            "error_type": "database_connectivity",
            "affected_service": "user-service",
            "severity": "high",
            "environment": "production",
            "logs": [
                "ERROR: connection to server on socket timeout",
                "SQLSTATE: 08006 connection failure",
                "Connection attempt failed"
            ],
            "metrics": {"response_time": 30000, "error_rate": 0.8}
        },
        {
            "id": "inc_002", 
            "title": "High Memory Usage Alert",
            "description": "Service consuming 95% of available memory, causing performance degradation",
            "error_type": "resource_exhaustion",
            "affected_service": "api-gateway",
            "severity": "medium",
            "environment": "production",
            "logs": [
                "WARNING: Memory usage at 95%",
                "GC pressure detected",
                "OutOfMemoryError in thread pool"
            ],
            "metrics": {"memory_usage": 0.95, "cpu_usage": 0.7}
        },
        {
            "id": "inc_003",
            "title": "Authentication Service Down",
            "description": "Auth service returning 500 errors, users cannot login",
            "error_type": "service_unavailable",
            "affected_service": "auth-service",
            "severity": "critical",
            "environment": "production", 
            "logs": [
                "HTTP 500 Internal Server Error",
                "Auth service health check failed",
                "Circuit breaker opened"
            ],
            "metrics": {"error_rate": 1.0, "response_time": 5000}
        },
        {
            "id": "inc_004",
            "title": "Network Timeout Issues",
            "description": "External API calls timing out, causing cascading failures",
            "error_type": "network_timeout",
            "affected_service": "payment-service",
            "severity": "high",
            "environment": "production",
            "logs": [
                "ERROR: Request timeout after 30s",
                "WARNING: Circuit breaker threshold reached",
                "External API endpoint unreachable"
            ],
            "metrics": {"timeout_rate": 0.6, "response_time": 35000}
        },
        {
            "id": "inc_005",
            "title": "SSL Certificate Expired",
            "description": "SSL certificate has expired, causing HTTPS failures",
            "error_type": "authentication_failure",
            "affected_service": "web-frontend",
            "severity": "critical",
            "environment": "production",
            "logs": [
                "ERROR: SSL certificate expired",
                "WARNING: Security alert - certificate invalid",
                "HTTPS connections failing"
            ],
            "metrics": {"ssl_errors": 1.0, "connection_failures": 0.9}
        },
        {
            "id": "inc_006",
            "title": "Disk Space Exhaustion",
            "description": "Application logs consuming all available disk space",
            "error_type": "resource_exhaustion",
            "affected_service": "logging-service",
            "severity": "medium",
            "environment": "staging",
            "logs": [
                "ERROR: No space left on device",
                "WARNING: Disk usage at 98%",
                "Log rotation failed"
            ],
            "metrics": {"disk_usage": 0.98, "log_size_gb": 45}
        }
    ]
    
    # Sample solutions
    sample_solutions = [
        {
            "id": "sol_001",
            "incident_id": "inc_001",
            "title": "Restart Database Connection Pool",
            "description": "Reset connection pool to resolve stale connections and improve database connectivity",
            "steps": [
                "Check database server status and connectivity",
                "Stop application gracefully to close existing connections",
                "Clear connection pool cache and reset pool settings",
                "Restart application with fresh connection pool",
                "Verify connectivity with test query",
                "Monitor connection metrics for 5 minutes"
            ],
            "effectiveness_score": 0.85,
            "usage_count": 15,
            "success_rate": 0.87,
            "tags": ["database", "connection", "pool"]
        },
        {
            "id": "sol_002",
            "incident_id": "inc_002",
            "title": "Scale Service Horizontally",
            "description": "Add more instances to handle memory pressure and distribute load",
            "steps": [
                "Check current resource usage across all instances",
                "Identify instances with highest memory pressure",
                "Scale up service instances by 50%",
                "Enable load balancing with health checks",
                "Monitor memory distribution across instances",
                "Verify performance improvement"
            ],
            "effectiveness_score": 0.9,
            "usage_count": 8,
            "success_rate": 0.92,
            "tags": ["scaling", "memory", "performance"]
        },
        {
            "id": "sol_003",
            "incident_id": "inc_003", 
            "title": "Restart Auth Service",
            "description": "Perform graceful restart of authentication service to resolve service errors",
            "steps": [
                "Check auth service logs for error patterns",
                "Notify users about temporary service interruption",
                "Perform graceful restart with rolling deployment",
                "Verify service health endpoints",
                "Test authentication flow with test credentials",
                "Monitor error rates for 10 minutes"
            ],
            "effectiveness_score": 0.75,
            "usage_count": 12,
            "success_rate": 0.83,
            "tags": ["auth", "service", "restart"]
        },
        {
            "id": "sol_004",
            "incident_id": "inc_004",
            "title": "Implement Circuit Breaker Pattern",
            "description": "Add circuit breaker to handle external API timeouts gracefully",
            "steps": [
                "Analyze external API timeout patterns",
                "Configure circuit breaker with appropriate thresholds",
                "Implement fallback mechanisms for failed requests",
                "Update timeout settings to 15 seconds",
                "Test circuit breaker behavior with simulated failures",
                "Monitor timeout rates and circuit breaker state"
            ],
            "effectiveness_score": 0.88,
            "usage_count": 6,
            "success_rate": 0.91,
            "tags": ["network", "timeout", "circuit-breaker"]
        },
        {
            "id": "sol_005",
            "incident_id": "inc_005",
            "title": "Renew SSL Certificate",
            "description": "Replace expired SSL certificate with new valid certificate",
            "steps": [
                "Generate new SSL certificate request",
                "Submit CSR to certificate authority",
                "Download and install new certificate",
                "Update certificate in load balancer configuration",
                "Test HTTPS connections with new certificate",
                "Verify certificate validity and expiration date"
            ],
            "effectiveness_score": 0.95,
            "usage_count": 3,
            "success_rate": 0.97,
            "tags": ["ssl", "security", "certificate"]
        },
        {
            "id": "sol_006",
            "incident_id": "inc_006",
            "title": "Implement Log Rotation and Cleanup",
            "description": "Set up automated log rotation and cleanup to prevent disk space issues",
            "steps": [
                "Stop logging service to prevent further disk usage",
                "Compress and archive old log files",
                "Configure log rotation with daily rotation and 7-day retention",
                "Clean up temporary files and cache",
                "Restart logging service with new configuration",
                "Monitor disk usage and log file sizes"
            ],
            "effectiveness_score": 0.82,
            "usage_count": 10,
            "success_rate": 0.85,
            "tags": ["logging", "disk-space", "cleanup"]
        }
    ]
    
    # Load data into similarity engine
    for inc_data in sample_incidents:
        incident = Incident(
            id=inc_data["id"],
            title=inc_data["title"],
            description=inc_data["description"],
            error_type=inc_data["error_type"],
            affected_service=inc_data["affected_service"],
            severity=inc_data["severity"],
            timestamp=datetime.now(),
            environment=inc_data["environment"],
            logs=inc_data["logs"],
            metrics=inc_data["metrics"]
        )
        
        # Find matching solution with error handling
        matching_solutions = [s for s in sample_solutions if s["incident_id"] == inc_data["id"]]
        if matching_solutions:
            solution_data = matching_solutions[0]
            solution = Solution(**solution_data)
            similarity_engine.add_incident(incident, solution)
        else:
            # Add incident without solution if no matching solution found
            print(f"⚠️  Warning: No solution found for incident {inc_data['id']}")
            similarity_engine.add_incident(incident, None)

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: IncidentRequest):
    """Get troubleshooting recommendations for an incident"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Create incident object
        incident = Incident(
            id=f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=request.title,
            description=request.description,
            error_type=request.error_type,
            affected_service=request.affected_service,
            severity=request.severity,
            timestamp=datetime.now(),
            environment=request.environment,
            logs=request.logs,
            metrics=request.metrics
        )
        
        # Get recommendations
        recommendations = similarity_engine.recommend_solutions(incident, top_k=3)
        
        # Format response
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                "solution": rec.solution.to_dict(),
                "confidence_score": round(rec.confidence_score, 3),
                "similarity_score": round(rec.similarity_score, 3),
                "context_match": round(rec.context_match, 3),
                "reasoning": rec.reasoning,
                "similar_incidents": rec.similar_incidents
            })
        
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        return RecommendationResponse(
            recommendations=formatted_recommendations,
            processing_time_ms=processing_time,
            similar_incidents_count=len(similarity_engine.incidents)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback on recommendation effectiveness"""
    # Update solution effectiveness based on feedback
    for solution in similarity_engine.solutions:
        if solution.id == feedback.solution_id:
            solution.usage_count += 1
            if feedback.was_helpful:
                # Increase effectiveness score
                solution.effectiveness_score = min(
                    1.0, 
                    solution.effectiveness_score + 0.1
                )
                solution.success_rate = (
                    solution.success_rate * (solution.usage_count - 1) + 1
                ) / solution.usage_count
            else:
                # Decrease effectiveness score
                solution.effectiveness_score = max(
                    0.1,
                    solution.effectiveness_score - 0.05
                )
                solution.success_rate = (
                    solution.success_rate * (solution.usage_count - 1)
                ) / solution.usage_count
            break
    
    return {"status": "feedback_recorded", "message": "Thank you for your feedback"}

@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_solution(request: ExecuteRequest):
    """Execute a solution and simulate the resolution process"""
    start_time = asyncio.get_event_loop().time()
    execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Find the solution to execute
        solution = None
        for s in similarity_engine.solutions:
            if s.id == request.solution_id:
                solution = s
                break
        
        if not solution:
            raise HTTPException(status_code=404, detail="Solution not found")
        
        # Simulate execution of each step
        steps_executed = []
        execution_logs = []
        success = True
        
        for i, step in enumerate(solution.steps):
            step_start = asyncio.get_event_loop().time()
            
            # Simulate step execution with realistic delays
            await asyncio.sleep(0.5)  # Simulate processing time
            
            step_success = True
            step_logs = []
            
            # Simulate different types of steps
            if "restart" in step.lower():
                step_logs.append(f"INFO: Restarting service...")
                step_logs.append(f"INFO: Service restart completed successfully")
            elif "check" in step.lower() or "verify" in step.lower():
                step_logs.append(f"INFO: Checking system status...")
                step_logs.append(f"INFO: Verification completed - status OK")
            elif "update" in step.lower() or "upgrade" in step.lower():
                step_logs.append(f"INFO: Updating configuration...")
                step_logs.append(f"INFO: Configuration update completed")
            elif "clear" in step.lower() or "clean" in step.lower():
                step_logs.append(f"INFO: Clearing cache/memory...")
                step_logs.append(f"INFO: Cache cleared successfully")
            else:
                step_logs.append(f"INFO: Executing step: {step}")
                step_logs.append(f"INFO: Step completed successfully")
            
            # Simulate occasional failures (10% chance)
            if np.random.random() < 0.1:
                step_success = False
                step_logs.append(f"ERROR: Step failed - retrying...")
                step_logs.append(f"INFO: Retry successful")
                step_success = True  # Retry succeeds
            
            step_time = int((asyncio.get_event_loop().time() - step_start) * 1000)
            
            steps_executed.append({
                "step_number": i + 1,
                "description": step,
                "status": "completed" if step_success else "failed",
                "execution_time_ms": step_time,
                "logs": step_logs
            })
            
            execution_logs.extend(step_logs)
            
            if not step_success:
                success = False
        
        # Add final status logs
        if success:
            execution_logs.append(f"SUCCESS: Solution execution completed successfully")
            execution_logs.append(f"INFO: Incident resolved in {len(solution.steps)} steps")
        else:
            execution_logs.append(f"WARNING: Solution execution completed with some failures")
        
        execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        return ExecuteResponse(
            execution_id=execution_id,
            status="completed" if success else "completed_with_warnings",
            steps_executed=steps_executed,
            execution_time_ms=execution_time,
            success=success,
            logs=execution_logs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_incidents": len(similarity_engine.incidents),
        "total_solutions": len(similarity_engine.solutions),
        "model_status": "ready",
        "average_solution_effectiveness": sum(s.effectiveness_score for s in similarity_engine.solutions) / len(similarity_engine.solutions) if similarity_engine.solutions else 0
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "troubleshooting-ai"}
