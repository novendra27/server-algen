"""
main.py
FastAPI application - REST API & WebSocket endpoints
"""

import asyncio
import uuid
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    OptimizationRequest,
    OptimizationResponse,
    WebSocketMessage,
    OptimizationResult
)
from ga_engine import run_genetic_algorithm


# ========================================
# FASTAPI APP INITIALIZATION
# ========================================

app = FastAPI(
    title="GA KKM Optimization API",
    description="REST API dan WebSocket untuk optimasi penentuan kelompok KKM menggunakan Algoritma Genetika",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Untuk production, ganti dengan domain spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# IN-MEMORY JOB STORAGE
# ========================================

# Dictionary untuk menyimpan status job
active_jobs: Dict[str, Dict[str, Any]] = {}

# Dictionary untuk menyimpan hasil job
job_results: Dict[str, Dict[str, Any]] = {}


# ========================================
# BACKGROUND TASK - PROCESS OPTIMIZATION
# ========================================

async def process_optimization(job_id: str, data: list, parameters: dict):
    """
    Background task untuk menjalankan algoritma genetika
    """
    try:
        # Update status
        active_jobs[job_id]["status"] = "processing"
        
        # Run GA (blocking operation, tapi di background task tidak masalah)
        result = run_genetic_algorithm(data, parameters)
        
        # Store result
        active_jobs[job_id]["status"] = "completed"
        job_results[job_id] = {
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        # Handle error
        active_jobs[job_id]["status"] = "failed"
        job_results[job_id] = {
            "status": "failed",
            "error": str(e),
            "message": "Optimization gagal"
        }


# ========================================
# REST API ENDPOINT
# ========================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GA KKM Optimization API",
        "version": "1.0.0",
        "endpoints": {
            "optimize": "POST /api/optimize",
            "websocket": "WS /ws/{job_id}"
        }
    }


@app.post("/api/optimize", response_model=OptimizationResponse)
async def create_optimization_job(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Endpoint untuk membuat optimization job
    
    - Validasi data mahasiswa
    - Generate job_id
    - Create background task
    - Return job_id untuk tracking via WebSocket
    """
    try:
        # Additional validation
        if len(request.data) == 0:
            raise HTTPException(status_code=400, detail="Data mahasiswa tidak boleh kosong")
        
        if len(request.data) < request.parameters.jumlah_kelompok:
            raise HTTPException(
                status_code=400,
                detail=f"Jumlah mahasiswa ({len(request.data)}) harus >= jumlah kelompok ({request.parameters.jumlah_kelompok})"
            )
        
        # Generate job_id
        job_id = str(uuid.uuid4())
        
        # Store job info
        active_jobs[job_id] = {
            "status": "queued",
            "created_at": asyncio.get_event_loop().time()
        }
        
        # Convert Pydantic models to dict for GA engine
        data_list = [mahasiswa.model_dump() for mahasiswa in request.data]
        parameters_dict = request.parameters.model_dump()
        
        # Add background task
        background_tasks.add_task(process_optimization, job_id, data_list, parameters_dict)
        
        # Return response
        return OptimizationResponse(
            job_id=job_id,
            status="queued",
            message="Job optimization berhasil dibuat. Gunakan WebSocket dengan job_id ini untuk menerima hasil."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ========================================
# WEBSOCKET ENDPOINT
# ========================================

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint untuk menerima hasil optimasi
    
    - Accept connection
    - Polling job status setiap 1 detik
    - Kirim hasil ketika completed
    - Cleanup dan close connection
    """
    await websocket.accept()
    
    try:
        # Check if job exists
        if job_id not in active_jobs:
            error_message = WebSocketMessage(
                status="error",
                message="Job ID tidak ditemukan"
            )
            await websocket.send_json(error_message.model_dump(exclude_none=True))
            await websocket.close()
            return
        
        # Send initial status
        initial_message = WebSocketMessage(
            status=active_jobs[job_id]["status"],
            message="Menunggu hasil optimasi..."
        )
        await websocket.send_json(initial_message.model_dump(exclude_none=True))
        
        # Polling loop
        while True:
            await asyncio.sleep(1)  # Poll every 1 second
            
            # Check if job is completed
            if job_id in job_results:
                result_data = job_results[job_id]
                
                if result_data["status"] == "completed":
                    # Send success result
                    success_message = WebSocketMessage(
                        status="completed",
                        result=OptimizationResult(**result_data["result"])
                    )
                    await websocket.send_json(success_message.model_dump(exclude_none=True))
                    
                elif result_data["status"] == "failed":
                    # Send error
                    error_message = WebSocketMessage(
                        status="failed",
                        error=result_data.get("error", "Unknown error"),
                        message=result_data.get("message", "Optimization gagal")
                    )
                    await websocket.send_json(error_message.model_dump(exclude_none=True))
                
                # Cleanup after 2 seconds
                await asyncio.sleep(2)
                
                # Remove from storage
                if job_id in active_jobs:
                    del active_jobs[job_id]
                if job_id in job_results:
                    del job_results[job_id]
                
                # Close connection
                await websocket.close()
                break
            
            # Check if still processing
            if job_id in active_jobs and active_jobs[job_id]["status"] == "processing":
                # Optional: Send periodic update
                pass
    
    except Exception as e:
        error_message = WebSocketMessage(
            status="error",
            message=f"WebSocket error: {str(e)}"
        )
        try:
            await websocket.send_json(error_message.model_dump(exclude_none=True))
        except:
            pass
        finally:
            await websocket.close()


# ========================================
# HEALTH CHECK ENDPOINT
# ========================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_jobs": len(active_jobs),
        "pending_results": len(job_results)
    }


# ========================================
# RUN SERVER (for development)
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload saat development
        log_level="info"
    )
