import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.db import Base

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(100), default="general_research")
    status = Column(String(50), default="pending") # pending, running, completed, failed, needs_approval
    quality_score = Column(Float, nullable=True)
    quality_explanation = Column(Text, nullable=True)
    execution_duration = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    logs = relationship("AgentLogModel", back_populates="task", cascade="all, delete-orphan")
    sources = relationship("ResearchSourceModel", back_populates="task", cascade="all, delete-orphan")
    reports = relationship("GeneratedReportModel", back_populates="task", cascade="all, delete-orphan")

class AgentLogModel(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    status = Column(String(50), default="success") # success, error, running
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("TaskModel", back_populates="logs")

class ResearchSourceModel(Base):
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    snippet = Column(Text, nullable=True)
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("TaskModel", back_populates="sources")

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, docx, txt, csv
    file_size = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class GeneratedReportModel(Base):
    __tablename__ = "generated_reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    report_title = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    format = Column(String(20), nullable=False) # pdf, docx
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("TaskModel", back_populates="reports")