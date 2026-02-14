# API Algoritma Genetika - Optimasi KKM

REST API untuk optimasi penentuan kelompok Kuliah Kerja Mahasiswa (KKM) menggunakan Algoritma Genetika dengan integrasi database MySQL.

## 🌐 Aplikasi Web

Frontend web untuk API ini tersedia di: **[web-algen](https://github.com/novendra27/web-algen)**

## 🚀 Fitur

- ✅ Integrasi database MySQL dengan SQLAlchemy ORM
- ✅ REST API dengan FastAPI
- ✅ Background processing untuk algoritma genetika
- ✅ Automatic database table creation
- ✅ Penyimpanan hasil ke database
- ✅ CORS middleware untuk integrasi frontend

## 📋 Prerequisites

- Python 3.8+
- MySQL Server (via XAMPP atau standalone)
- Virtual Environment (recommended)

## 🛠️ Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/novendra27/api-algen-kkm.git
cd api-algen-kkm
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

# Linux/Mac
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup Database

1. Jalankan MySQL Server (via XAMPP atau standalone)
2. Buat database `algen_kkm`:
   ```sql
   CREATE DATABASE algen_kkm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Tabel akan dibuat otomatis saat aplikasi pertama kali dijalankan

### 6. Konfigurasi Environment

Copy file `.env.example` ke `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
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

atau dengan uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: **http://localhost:8000**

Dokumentasi API otomatis tersedia di:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### 1. Root Endpoint

**GET** `/`

Menampilkan informasi basic API dan daftar endpoint yang tersedia.

**Response:**
```json
{
  "message": "GA KKM Optimization API",
  "version": "1.0.0",
  "endpoints": {
    "optimize": "POST /api/optimize",
    "health": "GET /health"
  }
}
```

### 2. Create Optimization Job

**POST** `/api/optimize`

Membuat job optimasi baru. Data mahasiswa diambil otomatis dari database.

**Request Body:**
```json
{
  "parameters": {
    "popsize": 50,
    "generation": 100,
    "cr": 0.6,
    "mr": 0.4,
    "kriteria_penghentian": 0.95,
    "jumlah_kelompok": 10
  }
}
```

**Parameter Details:**
- `popsize`: Ukuran populasi (integer, > 0)
- `generation`: Jumlah generasi maksimal (integer, > 0)
- `cr`: Crossover rate (float, 0.0-1.0)
- `mr`: Mutation rate (float, 0.0-1.0)
- `kriteria_penghentian`: Target fitness untuk penghentian (float, 0.0-1.0)
- `jumlah_kelompok`: Jumlah kelompok yang diinginkan (integer, > 0)

**Response:**
```json
{
  "id_optimasi": 123,
  "status": "success",
  "message": "Optimasi berhasil dijalankan"
}
```

> **Note:** Algoritma genetika berjalan di background. Gunakan `id_optimasi` untuk tracking hasil melalui database atau frontend.

### 3. Health Check

**GET** `/health`

Mengecek status kesehatan API dan koneksi database.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_mahasiswa": 150,
  "total_optimasi": 25
}
```

## 🗄️ Database Schema

### Tabel `data`
Menyimpan data mahasiswa.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary Key, Auto Increment |
| `jenis_kelamin` | ENUM('LK', 'PR') | Jenis kelamin mahasiswa |
| `jurusan` | VARCHAR(100) | Nama jurusan |
| `htq` | ENUM('Ya', 'Tidak') | Status HTQ (Hafalan Tahfidz Quran) |
| `created_at` | DATETIME | Timestamp pembuatan |
| `updated_at` | DATETIME | Timestamp update terakhir |

### Tabel `optimasi`
Menyimpan parameter dan status setiap job optimasi.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary Key, Auto Increment |
| `status` | ENUM | Status: 'pending', 'processing', 'completed', 'failed' |
| `popsize` | INTEGER | Ukuran populasi GA |
| `generation` | INTEGER | Jumlah generasi maksimal |
| `cr` | DECIMAL(5,4) | Crossover rate |
| `mr` | DECIMAL(5,4) | Mutation rate |
| `kriteria_penghentian` | DECIMAL(5,4) | Target fitness |
| `jumlah_kelompok` | INTEGER | Jumlah kelompok yang diinginkan |
| `fitness_terbaik` | DECIMAL(10,6) | Fitness terbaik yang dicapai |
| `waktu_eksekusi` | INTEGER | Waktu eksekusi (detik) |
| `created_at` | DATETIME | Timestamp pembuatan |
| `updated_at` | DATETIME | Timestamp update terakhir |

### Tabel `kelompoks`
Menyimpan hasil pengelompokan mahasiswa.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary Key, Auto Increment |
| `id_optimasi` | BIGINT | Foreign Key -> optimasi.id |
| `id_data` | BIGINT | Foreign Key -> data.id |
| `kelompok` | INTEGER | Nomor kelompok (1, 2, 3, ...) |
| `created_at` | DATETIME | Timestamp pembuatan |
| `updated_at` | DATETIME | Timestamp update terakhir |

## 🔧 Struktur Project

```
api-algen-kkm/
├── main.py                     # Entry point aplikasi
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (dibuat manual)
├── .env.example                # Template environment variables
├── .gitignore                  # Git ignore file
├── README.md                   # Dokumentasi project
├── app/
│   ├── __init__.py            # App package
│   ├── main.py                # FastAPI application & routes
│   ├── models.py              # Pydantic models (request/response)
│   └── ga_engine.py           # Algoritma Genetika engine
├── database/
│   ├── __init__.py            # Database package
│   ├── database.py            # Database connection & session
│   └── models.py              # SQLAlchemy ORM models
└── konteks/
    ├── algen.ipynb            # Jupyter notebook (development)
    ├── api_context.md         # API context documentation
    ├── database.md            # Database schema documentation
    └── perubahan_implementasi.md  # Implementation notes
```

## 📝 Workflow

1. **Input Data**: Data mahasiswa disimpan di tabel `data` (via SQL insert atau aplikasi web)
2. **Request Optimasi**: Client mengirim request `POST /api/optimize` dengan parameter GA
3. **Create Job**: Server membuat record di tabel `optimasi` dengan status `pending`
4. **Background Processing**: Background task menjalankan algoritma genetika
   - Status di-update ke `processing`
   - GA iterasi hingga kriteria terpenuhi
5. **Save Results**: Hasil pengelompokan disimpan ke tabel `kelompoks`
6. **Complete**: Status di-update ke `completed` dengan fitness dan waktu eksekusi
7. **Retrieve Results**: Client mengambil hasil melalui query database atau aplikasi web

## 🧬 Algoritma Genetika

### Constraint yang Dioptimasi

1. **C1 - HTQ**: Minimal 1 anggota HTQ di setiap kelompok
2. **C2 - Heterogenitas Jurusan**: Jumlah jurusan berbeda > 50% ukuran kelompok
3. **C3 - Proporsi Gender**: Proporsi gender menyimpang ±10% dari proporsi ideal
4. **C4 - Ukuran Kelompok**: Ukuran kelompok sesuai expected size

### Operator Genetika

- **Encoding**: Permutation encoding (ID mahasiswa)
- **Crossover**: Partially Mapped Crossover (PMX)
- **Mutation**: Reciprocal Exchange Mutation
- **Selection**: Elitism replacement strategy

### Kriteria Penghentian

- Mencapai target fitness (`kriteria_penghentian`)
- Mencapai jumlah generasi maksimal

## 🐛 Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server...")
```

**Solusi:**
1. Pastikan MySQL server berjalan
2. Cek kredensial di file `.env`
3. Pastikan database `algen_kkm` sudah dibuat
4. Test koneksi: `mysql -u root -p -h localhost`

### Import Error

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solusi:**
```bash
# Pastikan virtual environment aktif
pip install -r requirements.txt --upgrade
```

### Port Already in Use

```
ERROR: [Errno 10048] Only one usage of each socket address is normally permitted
```

**Solusi:**
```bash
# Gunakan port berbeda
uvicorn app.main:app --reload --port 8001
```

### Timezone Warning

```
Warning: Naive datetime used
```

**Solusi:** Project sudah menggunakan `zoneinfo` untuk Asia/Jakarta timezone. Pastikan Python 3.9+ atau install `backports.zoneinfo`

## 🔗 Links

- **Web Application**: [web-algen](https://github.com/novendra27/web-algen)
- **API Documentation**: http://localhost:8000/docs (saat server berjalan)
