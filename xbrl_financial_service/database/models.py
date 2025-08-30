"""
SQLAlchemy database models
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text, Boolean,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped

Base = declarative_base()


class Filing(Base):
    """
    Represents an XBRL filing
    """
    __tablename__ = "filings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    cik = Column(String(20), nullable=False)
    ticker = Column(String(10), nullable=True)
    filing_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=False)
    form_type = Column(String(10), nullable=False)  # 10-K, 10-Q, etc.
    fiscal_year_end = Column(String(10), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facts: Mapped[List["Fact"]] = relationship("Fact", back_populates="filing", cascade="all, delete-orphan")
    calculations: Mapped[List["Calculation"]] = relationship("Calculation", back_populates="filing", cascade="all, delete-orphan")
    presentations: Mapped[List["Presentation"]] = relationship("Presentation", back_populates="filing", cascade="all, delete-orphan")
    taxonomy_elements: Mapped[List["TaxonomyElement"]] = relationship("TaxonomyElement", back_populates="filing", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_filing_cik_date", "cik", "period_end_date"),
        Index("idx_filing_company_date", "company_name", "period_end_date"),
        UniqueConstraint("cik", "period_end_date", "form_type", name="uq_filing_cik_period_form"),
    )
    
    def __repr__(self):
        return f"<Filing(id={self.id}, company='{self.company_name}', period_end='{self.period_end_date}')>"


class Fact(Base):
    """
    Represents a financial fact from XBRL data
    """
    __tablename__ = "facts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False)
    
    # Core fact data
    concept = Column(String(255), nullable=False)
    label = Column(Text, nullable=False)
    value = Column(String(50), nullable=True)  # Store as string to handle various types
    numeric_value = Column(Float, nullable=True)  # Parsed numeric value
    unit = Column(String(20), nullable=True)
    
    # Period information
    period = Column(String(50), nullable=False)
    period_type = Column(String(20), nullable=False)  # instant, duration
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    
    # XBRL metadata
    context_id = Column(String(100), nullable=False)
    decimals = Column(Integer, nullable=True)
    dimensions = Column(Text, nullable=True)  # JSON string of dimensions
    
    # Statement classification
    statement_type = Column(String(50), nullable=True)  # income_statement, balance_sheet, etc.
    
    # Relationships
    filing: Mapped["Filing"] = relationship("Filing", back_populates="facts")
    
    # Indexes
    __table_args__ = (
        Index("idx_fact_filing_concept", "filing_id", "concept"),
        Index("idx_fact_concept", "concept"),
        Index("idx_fact_statement_type", "statement_type"),
        Index("idx_fact_period", "period_start", "period_end"),
    )
    
    def __repr__(self):
        return f"<Fact(id={self.id}, concept='{self.concept}', value='{self.value}')>"


class Calculation(Base):
    """
    Represents calculation relationships between concepts
    """
    __tablename__ = "calculations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False)
    
    parent_concept = Column(String(255), nullable=False)
    child_concept = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    order_num = Column(Integer, nullable=False, default=0)
    role = Column(String(500), nullable=True)  # XBRL role URI
    
    # Relationships
    filing: Mapped["Filing"] = relationship("Filing", back_populates="calculations")
    
    # Indexes
    __table_args__ = (
        Index("idx_calc_filing_parent", "filing_id", "parent_concept"),
        Index("idx_calc_parent_child", "parent_concept", "child_concept"),
        UniqueConstraint("filing_id", "parent_concept", "child_concept", "role", name="uq_calc_relationship"),
    )
    
    def __repr__(self):
        return f"<Calculation(parent='{self.parent_concept}', child='{self.child_concept}', weight={self.weight})>"


class Presentation(Base):
    """
    Represents presentation hierarchy relationships
    """
    __tablename__ = "presentations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False)
    
    parent_concept = Column(String(255), nullable=False)
    child_concept = Column(String(255), nullable=False)
    order_num = Column(Integer, nullable=False, default=0)
    preferred_label = Column(String(500), nullable=True)
    role = Column(String(500), nullable=True)  # XBRL role URI
    
    # Relationships
    filing: Mapped["Filing"] = relationship("Filing", back_populates="presentations")
    
    # Indexes
    __table_args__ = (
        Index("idx_pres_filing_parent", "filing_id", "parent_concept"),
        Index("idx_pres_parent_child", "parent_concept", "child_concept"),
        Index("idx_pres_role_order", "role", "order_num"),
    )
    
    def __repr__(self):
        return f"<Presentation(parent='{self.parent_concept}', child='{self.child_concept}', order={self.order_num})>"


class TaxonomyElement(Base):
    """
    Represents XBRL taxonomy element definitions
    """
    __tablename__ = "taxonomy_elements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    substitution_group = Column(String(255), nullable=False)
    period_type = Column(String(20), nullable=False)  # instant, duration
    balance = Column(String(20), nullable=True)  # debit, credit
    abstract = Column(Boolean, default=False)
    nillable = Column(Boolean, default=True)
    
    # Relationships
    filing: Mapped["Filing"] = relationship("Filing", back_populates="taxonomy_elements")
    
    # Indexes
    __table_args__ = (
        Index("idx_element_filing_name", "filing_id", "name"),
        Index("idx_element_name", "name"),
        Index("idx_element_type", "type"),
        UniqueConstraint("filing_id", "name", name="uq_element_filing_name"),
    )
    
    def __repr__(self):
        return f"<TaxonomyElement(name='{self.name}', type='{self.type}')>"


class CompanyInfo(Base):
    """
    Extended company information
    """
    __tablename__ = "company_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cik = Column(String(20), nullable=False, unique=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    ticker = Column(String(10), nullable=True)
    sic = Column(String(10), nullable=True)
    fiscal_year_end = Column(String(10), nullable=True)
    
    # Contact information
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Industry classification
    industry = Column(String(255), nullable=True)
    sector = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_company_ticker", "ticker"),
        Index("idx_company_name", "name"),
        Index("idx_company_sic", "sic"),
    )
    
    def __repr__(self):
        return f"<CompanyInfo(cik='{self.cik}', name='{self.name}')>"