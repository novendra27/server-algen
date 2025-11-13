# 📡 API Documentation - GA KKM Optimization System

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Protocol:** HTTP/REST API & WebSocket

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket Endpoint](#websocket-endpoint)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Usage Examples](#usage-examples)

---

## 🎯 Overview

API ini menyediakan layanan optimasi penentuan kelompok KKM (Kuliah Kerja Mahasiswa) menggunakan Algoritma Genetika. Sistem menggunakan kombinasi REST API untuk submit job dan WebSocket untuk menerima hasil secara real-time.

### Flow Komunikasi

```
Client → POST /api/optimize → Server (generate job_id)
       ↓
Client ← {job_id, status: "queued"}
       ↓
Client → WebSocket /ws/{job_id} → Server
       ↓
Client ← {status: "processing", message: "..."}
       ↓
       ... GA running in background ...
       ↓
Client ← {status: "completed", result: {...}}
       ↓
Connection closed
```

---

## 🌐 REST API Endpoints

### 1. GET `/`

**Deskripsi:** Root endpoint untuk informasi API

#### Request
```http
GET / HTTP/1.1
Host: localhost:8000
```

#### Response
```json
{
  "message": "GA KKM Optimization API",
  "version": "1.0.0",
  "endpoints": {
    "optimize": "POST /api/optimize",
    "websocket": "WS /ws/{job_id}"
  }
}
```

#### Status Codes
- `200 OK`: Success

---

### 2. GET `/health`

**Deskripsi:** Health check endpoint untuk monitoring

#### Request
```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response
```json
{
  "status": "healthy",
  "active_jobs": 3,
  "pending_results": 1
}
```

#### Response Fields
- `status` (string): Status server ("healthy")
- `active_jobs` (integer): Jumlah job yang sedang aktif
- `pending_results` (integer): Jumlah hasil yang menunggu diambil

#### Status Codes
- `200 OK`: Server healthy

---

### 3. POST `/api/optimize`

**Deskripsi:** Submit optimization job untuk pembuatan kelompok KKM

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "parameters": {
    "popsize": 50,
    "generation": 100,
    "cr": 0.6,
    "mr": 0.4,
    "kriteria_penghentian": 0.95,
    "jumlah_kelompok": 10
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
    // ... more students
  ]
}
```

#### Request Parameters

**`parameters` Object:**

| Field | Type | Required | Range | Description |
|-------|------|----------|-------|-------------|
| `popsize` | integer | Yes | > 0 | Ukuran populasi algoritma genetika |
| `generation` | integer | Yes | > 0 | Jumlah generasi maksimal |
| `cr` | float | Yes | 0.0 - 1.0 | Crossover rate (tingkat persilangan) |
| `mr` | float | Yes | 0.0 - 1.0 | Mutation rate (tingkat mutasi) |
| `kriteria_penghentian` | float | Yes | 0.0 - 1.0 | Target fitness untuk penghentian otomatis |
| `jumlah_kelompok` | integer | Yes | > 0 | Jumlah kelompok yang diinginkan |

**`data` Array:**

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| `ID` | integer | Yes | Unique | ID unik mahasiswa |
| `Jenis_Kelamin` | string | Yes | "LK", "PR" | Jenis kelamin mahasiswa |
| `Jurusan` | string | Yes | Any | Nama jurusan mahasiswa |
| `HTQ` | string | Yes | "Ya", "Tidak" | Status HTQ (Hafalan Tahfidz Quran) |

**Normalisasi Otomatis:**
- `Jenis_Kelamin`: "L", "Laki", "M" → "LK" | "P", "Perempuan", "F" → "PR"
- `HTQ`: "Y", "1", "Lulus", "T", "True" → "Ya" | "N", "0", "False" → "Tidak"

#### Response (Success)

**Status Code:** `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Job optimization berhasil dibuat. Gunakan WebSocket dengan job_id ini untuk menerima hasil."
}
```

#### Response Fields
- `job_id` (string): UUID untuk tracking job via WebSocket
- `status` (string): Status job ("queued")
- `message` (string): Pesan informasi

#### Response (Error)

**Status Code:** `400 Bad Request`

```json
{
  "detail": "Jumlah mahasiswa (5) harus >= jumlah kelompok (10)"
}
```

**Status Code:** `422 Unprocessable Entity`

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

#### Validasi

**Automatic Validation:**
- ✅ Data tidak boleh kosong
- ✅ ID mahasiswa harus unique (tidak ada duplikat)
- ✅ Jumlah mahasiswa >= jumlah kelompok
- ✅ Semua parameter dalam range yang valid
- ✅ Jenis_Kelamin harus LK/PR (setelah normalisasi)
- ✅ HTQ harus Ya/Tidak (setelah normalisasi)

#### Status Codes
- `200 OK`: Job berhasil dibuat
- `400 Bad Request`: Validasi gagal (custom validation)
- `422 Unprocessable Entity`: Format data tidak valid (Pydantic validation)
- `500 Internal Server Error`: Server error

---

### 4. GET `/docs`

**Deskripsi:** Swagger UI interactive documentation

#### Request
```http
GET /docs HTTP/1.1
Host: localhost:8000
```

#### Response
- Interactive Swagger UI untuk testing API
- Auto-generated dari OpenAPI schema

---

## 🔌 WebSocket Endpoint

### WS `/ws/{job_id}`

**Deskripsi:** WebSocket endpoint untuk menerima hasil optimasi secara real-time

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{job_id}');
```

**Path Parameters:**
- `job_id` (string): UUID yang didapat dari POST /api/optimize

#### Message Flow

**1. Initial Status (Immediately after connect)**

```json
{
  "status": "queued",
  "message": "Menunggu hasil optimasi..."
}
```

Atau jika sudah mulai diproses:

```json
{
  "status": "processing",
  "message": "Menunggu hasil optimasi..."
}
```

**2. Polling Loop**
- Server polling setiap **1 detik**
- **TIDAK** mengirim message selama masih processing
- Client hanya perlu **menunggu**

**3. Final Result - Success**

```json
{
  "status": "completed",
  "result": {
    "kelompok_list": [
      [1, 4, 10, 15, 2, 7, 11, 9, 6, 3, 5, 12],
      [8, 13, 14, 16, 19, 20, 22, 25, 28, 30, 31],
      [17, 18, 21, 23, 24, 26, 27, 29, 32, 33, 34]
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

**Result Fields:**

**`kelompok_list`** (array of arrays):
- Array berisi array ID mahasiswa per kelompok
- Index 0 = Kelompok 1, Index 1 = Kelompok 2, dst.

**`statistics`** (object):
- `best_fitness` (int): Total fitness terbaik yang dicapai
- `best_normalized_fitness` (float): Fitness normalized (0.0 - 1.0)
- `total_generations` (int): Jumlah generasi yang dijalankan
- `execution_time_seconds` (float): Waktu eksekusi dalam detik
- `max_fitness` (int): Fitness maksimal yang mungkin (jumlah_kelompok × 4)

**`kelompok_details`** (array of objects):
- `kelompok_id` (int): ID kelompok (1, 2, 3, ...)
- `anggota` (array): List ID mahasiswa dalam kelompok
- `jumlah_anggota` (int): Jumlah anggota dalam kelompok
- `constraints` (object): Score constraint individual
  - `C1_HTQ` (int): 1 = ada HTQ, 0 = tidak ada HTQ
  - `C2_Heterogenitas_Jurusan` (int): 1 = memenuhi, 0 = tidak
  - `C3_Proporsi_Gender` (int): 1 = memenuhi, 0 = tidak
  - `C4_Jumlah_Anggota` (int): 1 = sesuai expected size, 0 = tidak
- `score` (int): Total constraint score (0-4)

**4. Final Result - Failed**

```json
{
  "status": "failed",
  "error": "Division by zero in fitness calculation",
  "message": "Optimization gagal"
}
```

**5. Error - Invalid Job ID**

```json
{
  "status": "error",
  "message": "Job ID tidak ditemukan"
}
```

#### Connection Lifecycle

```
1. Client connect
2. Server accept → send initial status
3. Polling loop (1s interval)
4. GA selesai → send result
5. Wait 2 seconds
6. Server cleanup job
7. Server close connection
```

**Total Messages Received:** 2 messages
- 1 initial status
- 1 final result

#### Close Codes

| Code | Reason |
|------|--------|
| 1000 | Normal closure (after sending result) |
| 1001 | Going away (server shutdown) |
| 1002 | Protocol error |

---

## 📦 Data Models

### GAParameters

```typescript
{
  popsize: number;              // > 0
  generation: number;           // > 0
  cr: number;                   // 0.0 - 1.0
  mr: number;                   // 0.0 - 1.0
  kriteria_penghentian: number; // 0.0 - 1.0
  jumlah_kelompok: number;      // > 0
}
```

### MahasiswaData

```typescript
{
  ID: number;                   // Unique
  Jenis_Kelamin: "LK" | "PR";
  Jurusan: string;
  HTQ: "Ya" | "Tidak";
}
```

### OptimizationRequest

```typescript
{
  parameters: GAParameters;
  data: MahasiswaData[];
}
```

### OptimizationResponse

```typescript
{
  job_id: string;               // UUID v4
  status: "queued";
  message: string;
}
```

### WebSocketMessage

```typescript
{
  status: "queued" | "processing" | "completed" | "failed" | "error";
  message?: string;
  result?: OptimizationResult;
  error?: string;
}
```

### OptimizationResult

```typescript
{
  kelompok_list: number[][];
  statistics: {
    best_fitness: number;
    best_normalized_fitness: number;
    total_generations: number;
    execution_time_seconds: number;
    max_fitness: number;
  };
  kelompok_details: KelompokDetail[];
}
```

### KelompokDetail

```typescript
{
  kelompok_id: number;
  anggota: number[];
  jumlah_anggota: number;
  constraints: {
    C1_HTQ: 0 | 1;
    C2_Heterogenitas_Jurusan: 0 | 1;
    C3_Proporsi_Gender: 0 | 1;
    C4_Jumlah_Anggota: 0 | 1;
  };
  score: number; // 0-4
}
```

---

## ⚠️ Error Handling

### HTTP Errors

| Status Code | Type | Description |
|-------------|------|-------------|
| 400 | Bad Request | Validasi bisnis gagal (jumlah mahasiswa, dll) |
| 422 | Unprocessable Entity | Format data tidak valid (Pydantic) |
| 500 | Internal Server Error | Server error (unexpected) |

### WebSocket Errors

**Scenario 1: Job ID tidak ditemukan**
```json
{
  "status": "error",
  "message": "Job ID tidak ditemukan"
}
```
- Connection langsung ditutup setelah message ini

**Scenario 2: GA execution error**
```json
{
  "status": "failed",
  "error": "Error message details",
  "message": "Optimization gagal"
}
```
- Connection ditutup setelah 2 detik

**Scenario 3: Job expired**
- Job sudah di-cleanup (>2 detik setelah selesai)
- Sama dengan Scenario 1

---

## 💡 Usage Examples

### Example 1: Complete Flow (JavaScript)

```javascript
// 1. Submit optimization job
const response = await fetch('http://localhost:8000/api/optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    parameters: {
      popsize: 50,
      generation: 100,
      cr: 0.6,
      mr: 0.4,
      kriteria_penghentian: 0.95,
      jumlah_kelompok: 10
    },
    data: [
      { ID: 1, Jenis_Kelamin: "LK", Jurusan: "TI", HTQ: "Ya" },
      { ID: 2, Jenis_Kelamin: "PR", Jurusan: "SI", HTQ: "Tidak" },
      // ... more data
    ]
  })
});

const { job_id } = await response.json();

// 2. Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/${job_id}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.status === 'completed') {
    console.log('Result:', data.result);
    console.log('Best Fitness:', data.result.statistics.best_fitness);
    console.log('Total Kelompok:', data.result.kelompok_list.length);
  }
};
```

### Example 2: Python Client

```python
import requests
import asyncio
import websockets
import json

# 1. Submit job
response = requests.post('http://localhost:8000/api/optimize', json={
    'parameters': {
        'popsize': 50,
        'generation': 100,
        'cr': 0.6,
        'mr': 0.4,
        'kriteria_penghentian': 0.95,
        'jumlah_kelompok': 10
    },
    'data': [
        {'ID': 1, 'Jenis_Kelamin': 'LK', 'Jurusan': 'TI', 'HTQ': 'Ya'},
        # ... more data
    ]
})

job_id = response.json()['job_id']

# 2. Connect WebSocket
async def receive_result():
    uri = f"ws://localhost:8000/ws/{job_id}"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            if data['status'] == 'completed':
                print('Result:', data['result'])
                break

asyncio.run(receive_result())
```

### Example 3: cURL

```bash
# Submit job
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "popsize": 50,
      "generation": 100,
      "cr": 0.6,
      "mr": 0.4,
      "kriteria_penghentian": 0.95,
      "jumlah_kelompok": 10
    },
    "data": [
      {"ID": 1, "Jenis_Kelamin": "LK", "Jurusan": "TI", "HTQ": "Ya"}
    ]
  }'

# Response:
# {"job_id":"550e8400-...","status":"queued","message":"..."}
```

---

## 📌 Best Practices

### 1. Error Handling
```javascript
try {
  const response = await fetch('/api/optimize', {...});
  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
  }
} catch (error) {
  console.error('Network Error:', error);
}
```

### 2. WebSocket Reconnection
```javascript
let reconnectAttempts = 0;
const maxReconnects = 3;

function connectWebSocket(jobId) {
  const ws = new WebSocket(`ws://localhost:8000/ws/${jobId}`);
  
  ws.onerror = () => {
    if (reconnectAttempts < maxReconnects) {
      reconnectAttempts++;
      setTimeout(() => connectWebSocket(jobId), 2000);
    }
  };
}
```

### 3. Timeout Handling
```javascript
const timeout = setTimeout(() => {
  console.log('Optimization timeout');
  ws.close();
}, 300000); // 5 minutes

ws.onmessage = (event) => {
  clearTimeout(timeout);
  // Handle message
};
```

---

## 🔧 Testing

### Interactive Testing
1. Buka **Swagger UI**: http://localhost:8000/docs
2. Test endpoint POST /api/optimize
3. Copy job_id dari response
4. Gunakan WebSocket tester: `test_complete.html`

### Load Testing
```bash
# Install dependencies
pip install locust

# Create locustfile.py with API tests
# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## 📝 Notes

1. **Job Lifetime**: Job di-cleanup 2 detik setelah result dikirim
2. **Polling Interval**: Server polling setiap 1 detik
3. **No Database**: Semua job disimpan in-memory (hilang jika server restart)
4. **Concurrent Jobs**: Server bisa handle multiple jobs bersamaan
5. **CORS**: Saat ini allow all origins (ubah untuk production)

---

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **HTML Tester**: `test_complete.html`

---

**Last Updated:** November 13, 2025  
**API Version:** 1.0.0  
**Author:** GA KKM Development Team
