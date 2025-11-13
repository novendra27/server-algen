# 🔍 WebSocket Debugging Guide

## 📝 Cara Debug WebSocket

Ada **3 cara** untuk debugging WebSocket connection:

---

## 1️⃣ **HTML Debugger (TERMUDAH)** ✨

### Langkah-langkah:
1. **Buka file**: `test_websocket.html` di browser
2. **Kirim request** ke `POST /api/optimize` terlebih dahulu (via Swagger UI atau Postman)
3. **Copy job_id** dari response
4. **Paste** job_id ke field di HTML debugger
5. **Klik** "Connect WebSocket"
6. **Tunggu** hasil muncul real-time!

### Kelebihan:
- ✅ Visual yang bagus
- ✅ Tidak perlu coding
- ✅ Real-time message display
- ✅ Auto-format JSON

---

## 2️⃣ **Python Script**

### Install dependency:
```bash
pip install websockets
```

### Jalankan:
```bash
python test_websocket.py
```

### Edit job_id:
Buka `test_websocket.py` dan ganti nilai `job_id` di line ~99:
```python
job_id = "YOUR-JOB-ID-HERE"
```

### Kelebihan:
- ✅ Mudah di-customize
- ✅ Bisa log ke file
- ✅ Cocok untuk automated testing

---

## 3️⃣ **Browser DevTools (Manual)**

### Langkah-langkah:
1. Buka **Chrome DevTools** (F12)
2. Masuk tab **Console**
3. Paste kode berikut:

```javascript
// Ganti dengan job_id Anda
const jobId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/ws/${jobId}`);

ws.onopen = () => {
    console.log("✅ Connected!");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📨 Message received:", data);
    
    if (data.status === "completed") {
        console.log("🎉 Optimization completed!");
        console.log("📊 Statistics:", data.result.statistics);
        console.log("👥 Kelompok List:", data.result.kelompok_list);
    }
};

ws.onerror = (error) => {
    console.error("❌ Error:", error);
};

ws.onclose = (event) => {
    console.log("🔌 Connection closed:", event.code, event.reason);
};
```

### Kelebihan:
- ✅ Tidak perlu file tambahan
- ✅ Quick & dirty testing
- ✅ Built-in di browser

---

## 4️⃣ **Postman / Insomnia**

### Di Postman:
1. Buat **New Request** → **WebSocket Request**
2. URL: `ws://localhost:8000/ws/YOUR-JOB-ID`
3. Click **Connect**
4. Lihat messages di panel bawah

### Kelebihan:
- ✅ Professional tool
- ✅ Save & share requests
- ✅ Team collaboration

---

## 🎯 **Complete Testing Flow**

```
┌─────────────────────────────────────────────────────┐
│  1. POST /api/optimize                              │
│     → Get job_id: "550e8400-..."                   │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  2. Connect WebSocket                               │
│     ws://localhost:8000/ws/550e8400-...            │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  3. Receive Messages                                │
│     - Status: processing                            │
│     - Status: completed (with result)               │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  4. Connection Auto-Close                           │
│     (after sending result + 2 seconds)              │
└─────────────────────────────────────────────────────┘
```

---

## 📊 **Message Format**

### Processing:
```json
{
  "status": "processing",
  "message": "Menunggu hasil optimasi..."
}
```

### Completed:
```json
{
  "status": "completed",
  "result": {
    "kelompok_list": [[1,2,3], [4,5,6], ...],
    "statistics": {
      "best_fitness": 38,
      "best_normalized_fitness": 0.95,
      "total_generations": 45,
      "execution_time_seconds": 2.34,
      "max_fitness": 40
    },
    "kelompok_details": [...]
  }
}
```

### Failed:
```json
{
  "status": "failed",
  "error": "Error message",
  "message": "Optimization gagal"
}
```

---

## 🐛 **Troubleshooting**

### ❌ "Job ID tidak ditemukan"
- Job sudah expired (cleanup setelah 2 detik)
- Job ID salah
- **Solusi**: Kirim POST request baru, dapat job_id baru

### ❌ Connection refused
- Server belum jalan
- **Solusi**: `python main.py`

### ❌ No messages received
- GA masih processing (tunggu lebih lama)
- Background task error
- **Solusi**: Cek terminal server untuk error log

---

## 📁 Files

- `test_websocket.html` - HTML debugger (recommended)
- `test_websocket.py` - Python test script
- `DEBUG_WEBSOCKET.md` - This file

---

Selamat debugging! 🚀
