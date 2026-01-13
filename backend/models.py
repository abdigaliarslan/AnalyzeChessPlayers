from sqlalchemy import Column, Integer, String, ForeignKey, Text, UniqueConstraint, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String) 


class AnalysisStatus(enum.Enum):
    queued = "queued"
    done = "done"
    failed = "failed"
    exists = "exists"


class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, index=True)
    pgn_content = Column(String)
    normalized_pgn = Column(Text, nullable=False, index=True)
    pgn_hash = Column(String, nullable=False, index=True)
    result_text = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.queued)
    
    __table_args__ = (
        UniqueConstraint('pgn_hash', 'user_id', name='uq_pgn_hash_user'),
    )
