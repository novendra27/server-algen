"""
main.py
FastAPI application - REST API endpoints
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationResult
)
from app.ga_engine import run_genetic_algorithm
from database.database import get_db, engine
from database.models import Base, Data, Optimasi, Kelompok


# ========================================
# FASTAPI APP INITIALIZATION
# ========================================

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GA KKM Optimization API",
    description="REST API untuk optimasi penentuan kelompok KKM menggunakan Algoritma Genetika",
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

# Tidak diperlukan lagi - semua data disimpan di database


# ========================================
# BACKGROUND TASK - PROCESS OPTIMIZATION
# ========================================

async def process_optimization(optimasi_id: int, data: list, parameters: dict):
    """
    Background task untuk menjalankan algoritma genetika
    """
    from database.database import SessionLocal
    from database.models import Optimasi, Kelompok
    import time
    db = SessionLocal()
    
    try:
        # Get optimasi record
        optimasi = db.query(Optimasi).filter(Optimasi.id == optimasi_id).first()
        if not optimasi:
            return
        
        # Update status to processing
        optimasi.status = "processing"
        db.commit()
        
        # Record start time
        start_time = time.time()
        
        # Run GA
        result = run_genetic_algorithm(data, parameters)
        
        # Calculate execution time
        execution_time = int(time.time() - start_time)
        
        # Save results to database
        kelompok_list = result["kelompok_list"]
        for kelompok_idx, anggota_ids in enumerate(kelompok_list):
            for mahasiswa_id in anggota_ids:
                kelompok_entry = Kelompok(
                    id_optimasi=optimasi_id,
                    id_data=mahasiswa_id,
                    kelompok=kelompok_idx + 1  # Kelompok dimulai dari 1
                )
                db.add(kelompok_entry)
        
        # Update status to completed with fitness and execution time
        optimasi.status = "completed"
        optimasi.fitness_terbaik = result["statistics"]["best_normalized_fitness"]
        optimasi.waktu_eksekusi = execution_time
        db.commit()
        
    except Exception as e:
        # Handle error
        if optimasi:
            optimasi.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


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
            "health": "GET /health"
        }
    }


@app.post("/api/optimize", response_model=OptimizationResponse)
async def create_optimization_job(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk membuat optimization job
    
    - Mengambil data mahasiswa dari database
    - Validasi data
    - Membuat record optimasi
    - Menjalankan background task
    - Return status berhasil
    """
    try:
        # Fetch all data from database
        mahasiswa_list = db.query(Data).all()
        
        if len(mahasiswa_list) == 0:
            raise HTTPException(status_code=400, detail="Tidak ada data mahasiswa di database")
        
        # Convert to dict for GA engine
        data_list = [m.to_dict() for m in mahasiswa_list]
        
        # Validation
        if len(data_list) < request.parameters.jumlah_kelompok:
            raise HTTPException(
                status_code=400,
                detail=f"Jumlah mahasiswa ({len(data_list)}) harus >= jumlah kelompok ({request.parameters.jumlah_kelompok})"
            )
        
        # Create optimasi record
        optimasi = Optimasi(
            status="pending",
            popsize=request.parameters.popsize,
            generation=request.parameters.generation,
            cr=float(request.parameters.cr),
            mr=float(request.parameters.mr),
            kriteria_penghentian=float(request.parameters.kriteria_penghentian),
            jumlah_kelompok=request.parameters.jumlah_kelompok
        )
        db.add(optimasi)
        db.commit()
        db.refresh(optimasi)
        
        # Convert parameters to dict
        parameters_dict = request.parameters.model_dump()
        
        # Add background task
        background_tasks.add_task(process_optimization, optimasi.id, data_list, parameters_dict)
        
        # Return response
        return OptimizationResponse(
            id_optimasi=optimasi.id,
            status="success",
            message="Optimasi berhasil dijalankan"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ========================================
# HEALTH CHECK ENDPOINT
# ========================================

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        total_data = db.query(Data).count()
        total_optimasi = db.query(Optimasi).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_mahasiswa": total_data,
            "total_optimasi": total_optimasi
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
