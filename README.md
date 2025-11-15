# API Algoritma Genetika - Optimasi KKM

REST API untuk optimasi penentuan kelompok Kuliah Kerja Mahasiswa (KKM) menggunakan Algoritma Genetika dengan integrasi database MySQL.

## 🚀 Fitur

- ✅ Integrasi database MySQL
- ✅ REST API dengan FastAPI
- ✅ Background processing untuk algoritma genetika
- ✅ Tracking status optimasi
- ✅ Penyimpanan hasil ke database

## 📋 Prerequisites

- Python 3.8+
- MySQL Server (via XAMPP atau standalone)
- Virtual Environment

## 🛠️ Instalasi

### 1. Clone atau Download Project

```bash
cd "d:\Code Learning\Python Project\api-algen-kkm"
```

### 2. Buat Virtual Environment

```bash
python -m venv .venv
```

### 3. Aktivasi Virtual Environment

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup Database

1. Jalankan XAMPP dan aktifkan MySQL
2. Akses phpMyAdmin: http://localhost:8090/phpmyadmin
3. Buat database `algen_kkm`
4. Import/jalankan SQL schema dari `konteks/database.md`

### 6. Konfigurasi Environment

Copy file `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Edit `.env` dan sesuaikan kredensial database:

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/algen_kkm
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## 🏃 Menjalankan Server

```bash
python main.py
```

atau

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: http://localhost:8000

## 📚 API Endpoints

### 1. Root Endpoint

**GET** `/`

Response:
```json
{
  "message": "GA KKM Optimization API",
  "version": "1.0.0",
  "endpoints": {
    "optimize": "POST /api/optimize",
    "health": "GET /health",
    "data": "GET /api/data"
  }
}
```

### 2. Get All Data Mahasiswa

**GET** `/api/data`

Response:
```json
{
  "total": 100,
  "data": [
    {
      "ID": 1,
      "Jenis_Kelamin": "LK",
      "Jurusan": "Teknik Informatika",
      "HTQ": "Ya"
    }
  ]
}
```

### 3. Create Optimization Job

**POST** `/api/optimize`

Request Body:
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
  "data": []
}
```

> **Note:** Jika `data` kosong, akan mengambil semua data dari database

Response:
```json
{
  "job_id": "123",
  "status": "pending",
  "message": "Job optimization berhasil dibuat"
}
```

### 4. Check Optimization Status

**GET** `/api/optimize/{optimasi_id}/status`

Response:
```json
{
  "optimasi_id": 123,
  "status": "completed",
  "parameters": {
    "popsize": 50,
    "generation": 100,
    "cr": 0.6,
    "mr": 0.4,
    "kriteria_penghentian": 0.95,
    "jumlah_kelompok": 10
  },
  "created_at": "2025-11-14T10:00:00",
  "updated_at": "2025-11-14T10:05:00"
}
```

### 5. Get Optimization Result

**GET** `/api/optimize/{optimasi_id}/result`

Response:
```json
{
  "optimasi_id": 123,
  "status": "completed",
  "jumlah_kelompok": 10,
  "kelompok_list": [
    [1, 5, 12, 18, 25],
    [2, 7, 14, 20, 27],
    ...
  ],
  "created_at": "2025-11-14T10:00:00",
  "completed_at": "2025-11-14T10:05:00"
}
```

### 6. Health Check

**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "pending_jobs": 0,
  "processing_jobs": 1
}
```

## 🗄️ Database Schema

### Tabel `data`
- `id`: ID mahasiswa (Primary Key)
- `jenis_kelamin`: ENUM('LK', 'PR')
- `jurusan`: VARCHAR(100)
- `htq`: ENUM('Ya', 'Tidak')
- `created_at`, `updated_at`: Timestamps

### Tabel `optimasi`
- `id`: ID optimasi (Primary Key)
- `status`: ENUM('pending', 'processing', 'completed', 'failed')
- `popsize`, `generation`, `cr`, `mr`, `kriteria_penghentian`, `jumlah_kelompok`: Parameter GA
- `created_at`, `updated_at`: Timestamps

### Tabel `kelompoks`
- `id`: Primary Key
- `id_optimasi`: Foreign Key ke `optimasi`
- `id_data`: Foreign Key ke `data`
- `kelompok`: Nomor kelompok (1, 2, 3, ...)
- `created_at`, `updated_at`: Timestamps

## 🔧 Struktur Project

```
api-algen-kkm/
├── .env                    # Konfigurasi environment (jangan commit)
├── .env.example            # Template environment
├── .gitignore              # Git ignore file
├── database.py             # Database configuration
├── db_models.py            # SQLAlchemy ORM models
├── ga_engine.py            # Algoritma Genetika engine
├── main.py                 # FastAPI application
├── models.py               # Pydantic models
├── requirements.txt        # Python dependencies
└── konteks/
    ├── algen.ipynb        # Jupyter notebook
    ├── api_context_md.md  # API context
    └── database.md        # Database schema
```

## 📝 Workflow

1. Client mengirim request ke `/api/optimize` dengan parameter GA
2. Server membuat record di tabel `optimasi` dengan status `pending`
3. Background task menjalankan algoritma genetika
4. Status di-update ke `processing` saat GA berjalan
5. Hasil disimpan ke tabel `kelompoks`
6. Status di-update ke `completed`
7. Client bisa cek status via `/api/optimize/{id}/status`
8. Client bisa ambil hasil via `/api/optimize/{id}/result`

## 🐛 Troubleshooting

### Database Connection Error

1. Pastikan MySQL server berjalan
2. Cek kredensial di file `.env`
3. Pastikan database `algen_kkm` sudah dibuat

### Import Error

```bash
pip install -r requirements.txt --upgrade
```

### Port Already in Use

Ubah port di `.env` atau jalankan dengan port berbeda:

```bash
uvicorn main:app --reload --port 8001
```

## 📄 License

MIT License

## 👥 Author

Novendra27
