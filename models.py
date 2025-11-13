"""
models.py
Pydantic data models untuk request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


class GAParameters(BaseModel):
    """Model untuk parameter Algoritma Genetika"""
    popsize: int = Field(..., gt=0, description="Ukuran populasi")
    generation: int = Field(..., gt=0, description="Jumlah generasi maksimal")
    cr: float = Field(..., ge=0.0, le=1.0, description="Crossover rate (0.0-1.0)")
    mr: float = Field(..., ge=0.0, le=1.0, description="Mutation rate (0.0-1.0)")
    kriteria_penghentian: float = Field(..., ge=0.0, le=1.0, description="Target fitness untuk penghentian (0.0-1.0)")
    jumlah_kelompok: int = Field(..., gt=0, description="Jumlah kelompok KKM yang diinginkan")

    class Config:
        json_schema_extra = {
            "example": {
                "popsize": 50,
                "generation": 100,
                "cr": 0.6,
                "mr": 0.4,
                "kriteria_penghentian": 0.95,
                "jumlah_kelompok": 10
            }
        }


class MahasiswaData(BaseModel):
    """Model untuk data mahasiswa"""
    ID: int = Field(..., description="ID unik mahasiswa")
    Jenis_Kelamin: str = Field(..., description="Jenis kelamin: LK atau PR")
    Jurusan: str = Field(..., description="Nama jurusan mahasiswa")
    HTQ: str = Field(..., description="Status HTQ: Ya/Tidak/Y/T/1/0/Lulus")

    @field_validator('Jenis_Kelamin')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validasi dan normalisasi jenis kelamin"""
        v_upper = v.upper().strip()
        # Normalisasi ke LK atau PR
        if v_upper in ['LK', 'L', 'LAKI-LAKI', 'LAKI', 'M', 'MALE']:
            return 'LK'
        elif v_upper in ['PR', 'P', 'PEREMPUAN', 'F', 'FEMALE']:
            return 'PR'
        else:
            raise ValueError(f"Jenis kelamin harus LK atau PR, bukan '{v}'")

    @field_validator('HTQ')
    @classmethod
    def validate_htq(cls, v: str) -> str:
        """Validasi HTQ - terima berbagai format"""
        v_upper = str(v).upper().strip()
        # Semua variant yang valid
        valid_yes = ['YA', 'Y', '1', 'LULUS', 'TRUE', 'T']
        valid_no = ['TIDAK', 'N', '0', 'FALSE', 'F', 'BELUM']
        
        if v_upper in valid_yes:
            return 'Ya'
        elif v_upper in valid_no:
            return 'Tidak'
        else:
            raise ValueError(f"HTQ harus Ya/Tidak/Y/T/1/0/Lulus, bukan '{v}'")

    class Config:
        json_schema_extra = {
            "example": {
                "ID": 1,
                "Jenis_Kelamin": "LK",
                "Jurusan": "Teknik Informatika",
                "HTQ": "Ya"
            }
        }


class OptimizationRequest(BaseModel):
    """Model untuk request optimization"""
    parameters: GAParameters
    data: List[MahasiswaData]

    @field_validator('data')
    @classmethod
    def validate_data(cls, v: List[MahasiswaData]) -> List[MahasiswaData]:
        """Validasi data mahasiswa"""
        if len(v) == 0:
            raise ValueError("Data mahasiswa tidak boleh kosong")
        
        # Check duplicate IDs
        ids = [mahasiswa.ID for mahasiswa in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Ditemukan ID duplikat: {list(set(duplicates))}")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "popsize": 50,
                    "generation": 100,
                    "cr": 0.6,
                    "mr": 0.4,
                    "kriteria_penghentian": 0.95,
                    "jumlah_kelompok": 10
                },
                "data": [
                    {"ID": 1, "Jenis_Kelamin": "LK", "Jurusan": "Teknik Informatika", "HTQ": "Ya"},
                    {"ID": 2, "Jenis_Kelamin": "PR", "Jurusan": "Sistem Informasi", "HTQ": "Tidak"}
                ]
            }
        }


class OptimizationResponse(BaseModel):
    """Model untuk response optimization"""
    job_id: str
    status: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "message": "Job optimization berhasil dibuat. Gunakan WebSocket dengan job_id ini untuk menerima hasil."
            }
        }


class KelompokConstraints(BaseModel):
    """Model untuk constraint details per kelompok"""
    C1_HTQ: int = Field(..., description="Constraint HTQ (0 atau 1)")
    C2_Heterogenitas_Jurusan: int = Field(..., description="Constraint heterogenitas jurusan (0 atau 1)")
    C3_Proporsi_Gender: int = Field(..., description="Constraint proporsi gender (0 atau 1)")
    C4_Jumlah_Anggota: int = Field(..., description="Constraint jumlah anggota (0 atau 1)")


class KelompokDetail(BaseModel):
    """Model untuk detail kelompok"""
    kelompok_id: int
    anggota: List[int]
    jumlah_anggota: int
    constraints: KelompokConstraints
    score: int


class OptimizationStatistics(BaseModel):
    """Model untuk statistik hasil optimasi"""
    best_fitness: int
    best_normalized_fitness: float
    total_generations: int
    execution_time_seconds: float
    max_fitness: int


class OptimizationResult(BaseModel):
    """Model untuk hasil optimasi lengkap"""
    kelompok_list: List[List[int]] = Field(..., description="List of kelompok berisi ID mahasiswa")
    statistics: OptimizationStatistics
    kelompok_details: List[KelompokDetail]


class WebSocketMessage(BaseModel):
    """Model untuk WebSocket message"""
    status: str
    message: Optional[str] = None
    result: Optional[OptimizationResult] = None
    error: Optional[str] = None
