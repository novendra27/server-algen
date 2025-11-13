# Konteks Implementasi API Server
## Sistem Optimasi Penentuan Kelompok KKM dengan FastAPI

---

## 📋 DAFTAR ISI

1. [Overview Arsitektur](#1-overview-arsitektur)
2. [Teknologi Stack](#2-teknologi-stack)
3. [Struktur Project](#3-struktur-project)
4. [REST API Endpoint](#4-rest-api-endpoint)
5. [WebSocket Endpoint](#5-websocket-endpoint)
6. [Data Models](#6-data-models)
7. [Flow Diagram](#7-flow-diagram)
8. [Error Handling](#8-error-handling)
9. [Deployment Guide](#9-deployment-guide)
10. [Testing](#10-testing)

---

## 1. OVERVIEW ARSITEKTUR

### 1.1 Tujuan
Membangun RESTful API dan WebSocket server untuk:
- Menerima parameter GA dan data mahasiswa dari client
- Menjalankan algoritma genetika di background
- Mengirimkan hasil optimasi ke client via WebSocket

### 1.2 Arsitektur Pattern
- **REST API**: Untuk trigger optimization job
- **WebSocket**: Untuk mengirim hasil akhir optimasi
- **Background Task**: Asyncio untuk non-blocking execution
- **In-Memory Storage**: Dictionary untuk job tracking (tidak ada database)

### 1.3 Communication Flow
```
Client                    Server
  |                         |
  |---(1) POST /api/optimize-->|
  |<--(2) {job_id, status}---|
  |                         |
  |---(3) WS /ws/{job_id}---->|
  |                         |
  |                    (4) Run GA
  |                         |
  |<--(5) {result JSON}-----|
  |                         |
```

---

## 2. TEKNOLOGI STACK

### 2.1 Core Framework
- **FastAPI 0.104.1**: Modern async web framework
- **Uvicorn 0.24.0**: ASGI server dengan WebSocket support
- **Pydantic 2.5.0**: Data validation & serialization

### 2.2 Dependencies
- **pandas 2.1.3**: Data preprocessing
- **numpy 1.26.2**: Numerical operations
- **websockets 12.0**: WebSocket protocol
- **python-multipart 0.0.6**: Form data handling (optional)

### 2.3 Python Version
- **Python 3.8+** (required for FastAPI async features)

---

## 3. STRUKTUR PROJECT

```
ga-kkm-api/
│
├── main.py                 # FastAPI application & endpoints
├── ga_engine.py           # GA algorithm wrapper
├── models.py              # Pydantic data models
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (optional)
└── README.md             # Documentation
```

### 3.1 File Descriptions

#### `main.py`
- FastAPI app initialization
- CORS middleware configuration
- REST API endpoint `/api/optimize`
- WebSocket endpoint `/ws/{job_id}`
- Job management (active_jobs, job_results)

#### `ga_engine.py`
- Wrapper function `run_genetic_algorithm()`
- All GA helper functions (preprocessing, fitness, operators, etc.)
- Returns formatted result dict

#### `models.py`
- Pydantic models untuk request/response validation
- `GAParameters`: Parameter GA
- `MahasiswaData`: Data mahasiswa
- `OptimizationRequest`: Request body structure
- `OptimizationResponse`: Response body structure

---

## 4. REST API ENDPOINT

### 4.1 POST /api/optimize

#### Deskripsi
Endpoint untuk menerima parameter GA dan data mahasiswa, kemudian membuat optimization job.

#### Request
```http
POST /api/optimize HTTP/1.1
Content-Type: application/json

{
  "parameters": {
    "jumlah_kelompok": 10,
    "popsize": 50,
    "cr": 0.6,
    "mr": 0.4,
    "max_generation": 100,
    "target_fitness": 0.95
  },
  "data": [
    {
      "ID": 1,
      "Jenis_Kelamin": "LK",
      "Jurusan": "Teknik Informatika",
      "HTQ": "Ya"
    },
    {
      "ID": 2,
      "Jenis_Kelamin": "PR",
      "Jurusan": "Sistem Informasi",
      "HTQ": "Tidak"
    }
    // ... more data
  ]
}
```

#### Response (Success)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Job optimization berhasil dibuat. Gunakan WebSocket dengan job_id ini untuk menerima hasil."
}
```

#### Response (Error)
```json
{
  "detail": "Data mahasiswa tidak boleh kosong"
}
```

#### Validasi
- Parameter `jumlah_kelompok` > 0
- Jumlah mahasiswa >= jumlah_kelompok
- Tidak ada ID duplikat
- Jenis_Kelamin harus LK/PR
- HTQ harus Ya/Tidak/Y/T/1/0/Lulus

#### Status Codes
- `200`: Success
- `400`: Bad Request (validation error)
- `422`: Unprocessable Entity (invalid data type)
- `500`: Internal Server Error

---

## 5. WEBSOCKET ENDPOINT

### 5.1 WS /ws/{job_id}

#### Deskripsi
WebSocket endpoint untuk menerima hasil optimasi secara asynchronous.

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{job_id}');
```

#### Flow
1. Client connect dengan `job_id` dari REST API
2. Server accept connection dan kirim status awal
3. Server polling job status setiap 1 detik
4. Ketika job selesai, server kirim hasil akhir
5. Server cleanup job data dan close connection

#### Message Format

**Status Awal (Processing)**
```json
{
  "status": "processing",
  "message": "Menunggu hasil optimasi..."
}
```

**Hasil Akhir (Completed)**
```json
{
  "status": "completed",
  "result": {
    "kelompok_list": [
      [1, 4, 10, 15, 2, 7, 11, 9, 6, 3, 5, 12],
      [8, 13, 14, 16, 19, 20, 22, 25, 28, 30, 31]
    ],
    "statistics": {
      "best_fitness": 38,
      "best_normalized_fitness": 0.95,
      "total_generations": 45,
      "execution_time_seconds": 2.34,
      "max_fitness": 40
    },
    "kelompok_details": [
      {
        "kelompok_id": 1,
        "anggota": [1, 4, 10, 15, 2, 7, 11, 9, 6, 3, 5, 12],
        "jumlah_anggota": 12,
        "constraints": {
          "C1_HTQ": 1,
          "C2_Heterogenitas_Jurusan": 1,
          "C3_Proporsi_Gender": 1,
          "C4_Jumlah_Anggota": 1
        },
        "score": 4
      }
      // ... more groups
    ]
  }
}
```

**Error (Failed)**
```json
{
  "status": "failed",
  "error": "Error message",
  "message": "Optimization gagal"
}
```

**Invalid Job ID**
```json
{
  "status": "error",
  "message": "Job ID tidak ditemukan"
}
```

#### Polling Mechanism
- Server melakukan polling status job setiap **1 detik**
- Tidak ada real-time update per generasi
- Hanya kirim hasil final ketika job selesai

#### Auto Cleanup
- Setelah kirim hasil, server tunggu **2 detik**
- Kemudian hapus job dari `active_jobs` dan `job_results`
- WebSocket connection di-close

---

## 6. DATA MODELS

### 6.1 GAParameters
```python
{
  "jumlah_kelompok": int,      # > 0
  "popsize": int,              # > 0
  "cr": float,                 # [0.0, 1.0]
  "mr": float,                 # [0.0, 1.0]
  "max_generation": int,       # > 0
  "target_fitness": float      # [0.0, 1.0]
}
```

### 6.2 MahasiswaData
```python
{
  "ID": int,                   # Unique
  "Jenis_Kelamin": str,        # "LK" | "PR"
  "Jurusan": str,              # Any string
  "HTQ": str                   # "Ya" | "Tidak" | "Y" | "T" | "1" | "0" | "Lulus"
}
```

**Normalisasi Otomatis:**
- `Jenis_Kelamin`: "L" → "LK", "P" → "PR"
- `HTQ`: Semua variant di-convert ke binary (1/0) di preprocessing

### 6.3 OptimizationRequest
```python
{
  "parameters": GAParameters,
  "data": List[MahasiswaData]
}
```

**Validasi:**
- Data tidak boleh kosong
- Tidak ada ID duplikat
- Semua field required

### 6.4 OptimizationResponse
```python
{
  "job_id": str,               # UUID v4
  "status": str,               # "queued" | "processing" | "completed" | "failed"
  "message": str               # Info message
}
```

---

## 7. FLOW DIAGRAM

### 7.1 Complete Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ (1) POST /api/optimize
                           │     {parameters, data}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server                          │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  POST /api/optimize Endpoint                      │    │
│  │                                                    │    │
│  │  1. Validate request (Pydantic)                   │    │
│  │  2. Generate job_id (UUID)                        │    │
│  │  3. Store in active_jobs                          │    │
│  │  4. Create background task                        │    │
│  │  5. Return {job_id, status: "queued"}            │    │
│  └───────────────────────────────────────────────────┘    │
│                           │                                 │
│                           │ (2) Response                    │
│                           ▼                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ {job_id, status}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│                                                             │
│  1. Receive job_id                                         │
│  2. Connect WebSocket: ws://server/ws/{job_id}            │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ (3) WebSocket Connection
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server                          │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  Background Task: process_optimization()          │    │
│  │                                                    │    │
│  │  1. Update status: "processing"                   │    │
│  │  2. Run GA (run_genetic_algorithm)                │    │
│  │  3. Store result in job_results                   │    │
│  │  4. Update status: "completed"                    │    │
│  └───────────────────────────────────────────────────┘    │
│                           │                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │  WebSocket: /ws/{job_id}                          │    │
│  │                                                    │    │
│  │  1. Accept connection                             │    │
│  │  2. Send initial status                           │    │
│  │  3. Polling loop (every 1s)                       │    │
│  │     - Check job status                            │    │
│  │     - If completed: send result                   │    │
│  │     - If failed: send error                       │    │
│  │  4. Cleanup & close                               │    │
│  └───────────────────────────────────────────────────┘    │
│                           │                                 │
│                           │ (4) Result JSON                 │
│                           ▼                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ {status, result}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│                                                             │
│  1. Receive result                                         │
│  2. Display kelompok & statistics                          │
│  3. Close connection                                       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Job Lifecycle

```
┌──────────┐    POST     ┌──────────┐   Background   ┌────────────┐
│          │  /optimize  │          │      Task      │            │
│  Queued  │─────────────▶ Processing├────────────────▶ Completed  │
│          │             │          │                │            │
└──────────┘             └──────────┘                └────────────┘
                              │                            │
                              │ Error                      │
                              ▼                            ▼
                         ┌──────────┐              ┌────────────┐
                         │          │              │            │
                         │  Failed  │              │  Cleanup   │
                         │          │              │            │
                         └──────────┘              └────────────┘
```

---

## 8. ERROR HANDLING

### 8.1 Validation Errors (400)

**Trigger:**
- Data mahasiswa kosong
- Jumlah kelompok <= 0
- Jumlah mahasiswa < jumlah kelompok
- ID duplikat

**Response:**
```json
{
  "detail": "Error message describing the issue"
}
```

### 8.2 Pydantic Validation (422)

**Trigger:**
- Invalid data type
- Missing required field
- Value out of range (e.g., cr > 1.0)

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "parameters", "cr"],
      "msg": "ensure this value is less than or equal to 1.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### 8.3 WebSocket Errors

**Invalid Job ID:**
```json
{
  "status": "error",
  "message": "Job ID tidak ditemukan"
}
```

**GA Execution Error:**
```json
{
  "status": "failed",
  "error": "Division by zero in fitness calculation",
  "message": "Optimization gagal"
}
```

### 8.4 Server Error Handling

```python
try:
    # GA execution
    result = run_genetic_algorithm(data, parameters)
except Exception as e:
    # Catch all errors
    active_jobs[job_id]["status"] = "failed"
    job_results[job_id] = {
        "error": str(e),
        "message": "Optimization gagal"
    }
```

---

**END OF API CONTEXT DOCUMENT**

*Dokumen ini berisi panduan lengkap implementasi REST API dan WebSocket untuk sistem optimasi penentuan kelompok KKM menggunakan FastAPI.*