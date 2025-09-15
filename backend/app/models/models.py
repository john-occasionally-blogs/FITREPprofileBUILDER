from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.types import Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Officer(Base):
    __tablename__ = "officers"
    
    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_initial = Column(String(1))
    service_number = Column(String(20), unique=True, nullable=False)
    current_rank = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    fitreports = relationship("FitReport", back_populates="officer")
    rs_profiles = relationship("Profile", back_populates="reporting_senior")
    scoring_sessions = relationship("ScoringSession", back_populates="officer")

class FitReport(Base):
    __tablename__ = "fitreports"
    
    id = Column(Integer, primary_key=True, index=True)
    officer_id = Column(Integer, ForeignKey("officers.id"), nullable=False)
    fitrep_id = Column(String(50), nullable=False)
    report_date = Column(Date)
    period_from = Column(Date)
    period_to = Column(Date)
    rank_at_time = Column(String(20), nullable=False)
    organization = Column(String(200))
    reporting_senior_name = Column(String(100))
    reporting_senior_rank = Column(String(20))
    reviewing_officer_name = Column(String(100))
    reviewing_officer_rank = Column(String(20))
    occasion_type = Column(String(10), nullable=False)
    fra_score = Column(Numeric(3,2))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    officer = relationship("Officer", back_populates="fitreports")
    trait_scores = relationship("TraitScore", back_populates="fitrep")
    relative_values = relationship("RelativeValue", back_populates="fitrep")

class TraitScore(Base):
    __tablename__ = "trait_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    fitrep_id = Column(Integer, ForeignKey("fitreports.id"), nullable=False)
    trait_name = Column(String(50), nullable=False)
    trait_order = Column(Integer, nullable=False)
    score_letter = Column(String(1))
    score_numeric = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    fitrep = relationship("FitReport", back_populates="trait_scores")

class RelativeValue(Base):
    __tablename__ = "relative_values"
    
    id = Column(Integer, primary_key=True, index=True)
    fitrep_id = Column(Integer, ForeignKey("fitreports.id"), nullable=False)
    rank = Column(String(20), nullable=False)
    reporting_senior = Column(String(100), nullable=False)
    relative_value = Column(Integer)
    total_reports_for_rank = Column(Integer, nullable=False)
    highest_fra_for_rank = Column(Numeric(3,2))
    average_fra_for_rank = Column(Numeric(3,2))
    minimum_fra_for_rank = Column(Numeric(3,2))
    calculated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    fitrep = relationship("FitReport", back_populates="relative_values")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    reporting_senior_id = Column(Integer, ForeignKey("officers.id"), nullable=False)
    reporting_senior_name = Column(String(100), nullable=False)
    rank = Column(String(20), nullable=False)
    total_reports = Column(Integer, nullable=False)
    average_fra = Column(Numeric(3,2))
    highest_fra = Column(Numeric(3,2))
    lowest_fra = Column(Numeric(3,2))
    average_rv = Column(Numeric(3,2))
    highest_rv = Column(Integer)
    lowest_rv = Column(Integer)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reporting_senior = relationship("Officer", back_populates="rs_profiles")

class ScoringSession(Base):
    __tablename__ = "scoring_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    officer_id = Column(Integer, ForeignKey("officers.id"), nullable=False)
    session_name = Column(String(200))
    scenario_data = Column(JSON)
    predicted_impact = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    officer = relationship("Officer", back_populates="scoring_sessions")