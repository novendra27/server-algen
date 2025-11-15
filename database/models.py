"""
db_models.py
SQLAlchemy ORM models untuk database algen_kkm
"""

from sqlalchemy import Column, BigInteger, Integer, String, Enum, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from zoneinfo import ZoneInfo
from database.database import Base


def get_jakarta_time():
    """Get current time in Asia/Jakarta timezone"""
    return datetime.now(ZoneInfo("Asia/Jakarta"))


class Data(Base):
    """
    Model untuk tabel data (mahasiswa)
    """
    __tablename__ = "data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    jenis_kelamin = Column(Enum('LK', 'PR'), nullable=False)
    jurusan = Column(String(100), nullable=False)
    htq = Column(Enum('Ya', 'Tidak'), nullable=False)
    created_at = Column(DateTime, default=get_jakarta_time)
    updated_at = Column(DateTime, default=get_jakarta_time, onupdate=get_jakarta_time)
    
    # Relationship
    kelompoks = relationship("Kelompok", back_populates="data")
    
    def to_dict(self):
        """Convert to dictionary for GA engine"""
        return {
            "ID": self.id,
            "Jenis_Kelamin": self.jenis_kelamin,
            "Jurusan": self.jurusan,
            "HTQ": self.htq
        }


class Optimasi(Base):
    """
    Model untuk tabel optimasi
    """
    __tablename__ = "optimasi"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed'),
        nullable=False,
        default='pending'
    )
    popsize = Column(Integer, nullable=True)
    generation = Column(Integer, nullable=True)
    cr = Column(Numeric(5, 4), nullable=True)
    mr = Column(Numeric(5, 4), nullable=True)
    kriteria_penghentian = Column(Numeric(5, 4), nullable=True)
    jumlah_kelompok = Column(Integer, nullable=True)
    fitness_terbaik = Column(Numeric(10, 6), nullable=True)
    waktu_eksekusi = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=get_jakarta_time)
    updated_at = Column(DateTime, default=get_jakarta_time, onupdate=get_jakarta_time)
    
    # Relationship
    kelompoks = relationship("Kelompok", back_populates="optimasi")


class Kelompok(Base):
    """
    Model untuk tabel kelompoks (hasil pengelompokan)
    """
    __tablename__ = "kelompoks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    id_optimasi = Column(BigInteger, ForeignKey('optimasi.id'), nullable=False)
    id_data = Column(BigInteger, ForeignKey('data.id'), nullable=False)
    kelompok = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=get_jakarta_time)
    updated_at = Column(DateTime, default=get_jakarta_time, onupdate=get_jakarta_time)
    
    # Relationships
    optimasi = relationship("Optimasi", back_populates="kelompoks")
    data = relationship("Data", back_populates="kelompoks")
