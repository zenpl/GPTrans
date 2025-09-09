from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False, default="zh-CN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    glossary_id = Column(Integer, ForeignKey("glossaries.id"), nullable=True)
    
    # Relationships
    pages = relationship("Page", back_populates="book", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="book", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="book", cascade="all, delete-orphan")
    glossary = relationship("Glossary", back_populates="books")


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    index = Column(Integer, nullable=False)  # Page number in book
    image_url = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    dpi = Column(Integer, default=300)
    
    # Relationships
    book = relationship("Book", back_populates="pages")
    blocks = relationship("Block", back_populates="page", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    type = Column(String(20), nullable=False)  # heading, paragraph, caption, footnote, figure, page-number
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)
    order = Column(Integer, nullable=False)  # Reading order within page
    text_source = Column(Text, nullable=False)
    text_translated = Column(Text, nullable=True)
    spans = Column(JSON, default=list)  # Formatting spans
    refs = Column(JSON, default=list)   # References to other blocks
    status = Column(String(20), default="pending")  # pending, translating, translated, typeset
    
    # Relationships
    page = relationship("Page", back_populates="blocks")


class Glossary(Base):
    __tablename__ = "glossaries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    terms = relationship("GlossaryTerm", back_populates="glossary", cascade="all, delete-orphan")
    books = relationship("Book", back_populates="glossary")


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"
    
    id = Column(Integer, primary_key=True, index=True)
    glossary_id = Column(Integer, ForeignKey("glossaries.id"), nullable=False)
    src = Column(String, nullable=False)
    tgt = Column(String, nullable=False)
    case_sensitive = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    glossary = relationship("Glossary", back_populates="terms")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    type = Column(String(20), nullable=False)  # ocr, translate, typeset, export
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    logs = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="jobs")


class Export(Base):
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    formats = Column(JSON, nullable=False)  # ["pdf", "epub"]
    url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="exports")