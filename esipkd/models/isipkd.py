from sqlalchemy import (
    Column,
    Index,
    Integer,
    SmallInteger,
    Text,
    BigInteger,
    String,
    Float,
    DateTime
    )
from ..models import(
      DefaultModel,
      KodeModel,
      Base,
      
      )
#####################
#
###########################        
class PkbModel(DefaultModel,Base):
    __tablename__ = 'pkbs'
    id = Column(BigInteger, primary_key=True)
    nik = Column(String(16))
    no_rangka = Column(String(16))
    email = Column(String(32))
    mobile_phone = Column(String(16))

class UnitModel(DefaultModel,Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    kode = Column(String(16))
    uraian = Column(String(16))
    level_id = Column(SmallInteger)
    is_summary = Column(SmallInteger)
    parent_id = Column(SmallInteger)
    
class RekeningModel(DefaultModel,Base):
    __tablename__ = 'rekenings'
    id = Column(Integer, primary_key=True)
    kode = Column(String(16))
    uraian = Column(String(16))
    level_id = Column(SmallInteger)
    is_summary = Column(SmallInteger)
    parent_id = Column(SmallInteger)

class UnitRekeningModel(Base):
    __tablename__ = 'unit_rekenings'
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer)
    rekening_id = Column(Integer)
    
class SptpdModel(Base):
    __tablename__ = 'sptpds'
    id = Column(Integer, primary_key=True)
    no_bayar    = Column(String(16))
    tahun       = Column(Integer)
    bulan       = Column(Integer)
    unit_id     = Column(Integer)
    rekening_id = Column(Integer)
    kode        = Column(String(16))
    nama        = Column(String(32))
    alamat1     = Column(String(32))
    alamat2     = Column(String(32))
    omset       = Column(BigInteger)
    tarif       = Column(Float)
    pokok_pajak = Column(BigInteger)
    create_uid  = Column(Integer)
    update_uid  = Column(Integer)
    create_date = Column(DateTime(timezone=True))
    update_date = Column(DateTime(timezone=True))
    status_bayar = Column(SmallInteger)
    
    
