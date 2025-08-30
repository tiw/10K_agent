"""
Database operations and data access layer
"""

import json
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models import Base, Filing, Fact, Calculation, Presentation, TaxonomyElement, CompanyInfo
from .connection import create_engine, get_session
from ..models import (
    FilingData, FinancialFact, CalculationRelationship, 
    PresentationRelationship, TaxonomyElement as ModelTaxonomyElement,
    CompanyInfo as ModelCompanyInfo, StatementType, PeriodType
)
from ..config import Config
from ..utils.logging import get_logger
from ..utils.exceptions import DataValidationError, QueryError

logger = get_logger(__name__)


class DatabaseManager:
    """
    Main database operations manager
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.engine = create_engine(config=config)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return get_session(self.engine)
    
    def save_filing_data(self, filing_data: FilingData) -> int:
        """
        Save complete filing data to database
        
        Args:
            filing_data: FilingData object to save
            
        Returns:
            Filing ID
            
        Raises:
            DataValidationError: If data validation fails
        """
        with self.get_session() as session:
            try:
                # Check if filing already exists
                existing_filing = session.query(Filing).filter(
                    and_(
                        Filing.cik == filing_data.company_info.cik,
                        Filing.period_end_date == filing_data.period_end_date,
                        Filing.form_type == filing_data.form_type
                    )
                ).first()
                
                if existing_filing:
                    logger.info(f"Filing already exists for {filing_data.company_info.name} - {filing_data.period_end_date}")
                    return existing_filing.id
                
                # Create filing record
                filing = Filing(
                    company_name=filing_data.company_info.name,
                    cik=filing_data.company_info.cik,
                    ticker=filing_data.company_info.ticker,
                    filing_date=filing_data.filing_date,
                    period_end_date=filing_data.period_end_date,
                    form_type=filing_data.form_type,
                    fiscal_year_end=filing_data.company_info.fiscal_year_end
                )
                
                session.add(filing)
                session.flush()  # Get the filing ID
                
                # Save company info
                self._save_company_info(session, filing_data.company_info)
                
                # Save facts
                self._save_facts(session, filing.id, filing_data.all_facts)
                
                # Save calculations and presentations from statements
                for statement in [filing_data.income_statement, filing_data.balance_sheet, 
                                filing_data.cash_flow_statement, filing_data.shareholders_equity,
                                filing_data.comprehensive_income]:
                    if statement:
                        self._save_calculations(session, filing.id, statement.calculations)
                        self._save_presentations(session, filing.id, statement.presentation_order)
                
                # Save taxonomy elements
                self._save_taxonomy_elements(session, filing.id, filing_data.taxonomy_elements)
                
                session.commit()
                logger.info(f"Successfully saved filing data for {filing_data.company_info.name}")
                return filing.id
                
            except IntegrityError as e:
                session.rollback()
                raise DataValidationError(f"Data integrity error: {str(e)}")
            except SQLAlchemyError as e:
                session.rollback()
                raise DataValidationError(f"Database error: {str(e)}")
    
    def get_filing_by_id(self, filing_id: int) -> Optional[FilingData]:
        """
        Retrieve filing data by ID
        
        Args:
            filing_id: Filing ID
            
        Returns:
            FilingData object or None if not found
        """
        with self.get_session() as session:
            filing = session.query(Filing).filter(Filing.id == filing_id).first()
            if not filing:
                return None
            
            return self._convert_filing_to_model(session, filing)
    
    def get_filings_by_company(self, cik: str, limit: int = 10) -> List[FilingData]:
        """
        Get filings for a specific company
        
        Args:
            cik: Company CIK
            limit: Maximum number of filings to return
            
        Returns:
            List of FilingData objects
        """
        with self.get_session() as session:
            filings = session.query(Filing).filter(
                Filing.cik == cik
            ).order_by(desc(Filing.period_end_date)).limit(limit).all()
            
            return [self._convert_filing_to_model(session, filing) for filing in filings]
    
    def search_facts(
        self, 
        concept_pattern: Optional[str] = None,
        label_pattern: Optional[str] = None,
        statement_type: Optional[StatementType] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        cik: Optional[str] = None,
        limit: int = 100
    ) -> List[FinancialFact]:
        """
        Search for financial facts with various filters
        
        Args:
            concept_pattern: Pattern to match in concept names
            label_pattern: Pattern to match in labels
            statement_type: Filter by statement type
            period_start: Start date filter
            period_end: End date filter
            cik: Company CIK filter
            limit: Maximum results to return
            
        Returns:
            List of FinancialFact objects
        """
        with self.get_session() as session:
            query = session.query(Fact).join(Filing)
            
            # Apply filters
            if concept_pattern:
                query = query.filter(Fact.concept.ilike(f"%{concept_pattern}%"))
            
            if label_pattern:
                query = query.filter(Fact.label.ilike(f"%{label_pattern}%"))
            
            if statement_type:
                query = query.filter(Fact.statement_type == statement_type.value)
            
            if period_start:
                query = query.filter(Fact.period_start >= period_start)
            
            if period_end:
                query = query.filter(Fact.period_end <= period_end)
            
            if cik:
                query = query.filter(Filing.cik == cik)
            
            facts = query.order_by(desc(Fact.period_end)).limit(limit).all()
            
            return [self._convert_fact_to_model(fact) for fact in facts]
    
    def get_company_info(self, cik: str) -> Optional[ModelCompanyInfo]:
        """
        Get company information by CIK
        
        Args:
            cik: Company CIK
            
        Returns:
            CompanyInfo object or None if not found
        """
        with self.get_session() as session:
            company = session.query(CompanyInfo).filter(CompanyInfo.cik == cik).first()
            if not company:
                return None
            
            return ModelCompanyInfo(
                name=company.name,
                cik=company.cik,
                ticker=company.ticker,
                sic=company.sic,
                fiscal_year_end=company.fiscal_year_end,
                address=company.address,
                phone=company.phone
            )
    
    def _save_company_info(self, session: Session, company_info: ModelCompanyInfo):
        """Save or update company information"""
        existing = session.query(CompanyInfo).filter(CompanyInfo.cik == company_info.cik).first()
        
        if existing:
            # Update existing record
            existing.name = company_info.name
            existing.ticker = company_info.ticker
            existing.sic = company_info.sic
            existing.fiscal_year_end = company_info.fiscal_year_end
            existing.address = company_info.address
            existing.phone = company_info.phone
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            company = CompanyInfo(
                cik=company_info.cik,
                name=company_info.name,
                ticker=company_info.ticker,
                sic=company_info.sic,
                fiscal_year_end=company_info.fiscal_year_end,
                address=company_info.address,
                phone=company_info.phone
            )
            session.add(company)
    
    def _save_facts(self, session: Session, filing_id: int, facts: List[FinancialFact]):
        """Save financial facts"""
        for fact in facts:
            # Determine numeric value
            numeric_value = None
            if isinstance(fact.value, (int, float)):
                numeric_value = float(fact.value)
            elif isinstance(fact.value, str) and fact.value.replace('.', '').replace('-', '').isdigit():
                try:
                    numeric_value = float(fact.value)
                except ValueError:
                    pass
            
            # Serialize dimensions
            dimensions_json = json.dumps(fact.dimensions) if fact.dimensions else None
            
            db_fact = Fact(
                filing_id=filing_id,
                concept=fact.concept,
                label=fact.label,
                value=str(fact.value),
                numeric_value=numeric_value,
                unit=fact.unit,
                period=fact.period,
                period_type=fact.period_type.value,
                period_start=fact.period_start,
                period_end=fact.period_end,
                context_id=fact.context_id,
                decimals=fact.decimals,
                dimensions=dimensions_json
            )
            
            session.add(db_fact)
    
    def _save_calculations(self, session: Session, filing_id: int, calculations: List[CalculationRelationship]):
        """Save calculation relationships"""
        for calc in calculations:
            db_calc = Calculation(
                filing_id=filing_id,
                parent_concept=calc.parent,
                child_concept=calc.child,
                weight=calc.weight,
                order_num=calc.order,
                role=calc.role
            )
            session.add(db_calc)
    
    def _save_presentations(self, session: Session, filing_id: int, presentations: List[PresentationRelationship]):
        """Save presentation relationships"""
        for pres in presentations:
            db_pres = Presentation(
                filing_id=filing_id,
                parent_concept=pres.parent,
                child_concept=pres.child,
                order_num=pres.order,
                preferred_label=pres.preferred_label,
                role=pres.role
            )
            session.add(db_pres)
    
    def _save_taxonomy_elements(self, session: Session, filing_id: int, elements: List[ModelTaxonomyElement]):
        """Save taxonomy elements"""
        for element in elements:
            db_element = TaxonomyElement(
                filing_id=filing_id,
                name=element.name,
                type=element.type,
                substitution_group=element.substitution_group,
                period_type=element.period_type.value,
                balance=element.balance,
                abstract=element.abstract,
                nillable=element.nillable
            )
            session.add(db_element)
    
    def _convert_filing_to_model(self, session: Session, filing: Filing) -> FilingData:
        """Convert database Filing to FilingData model"""
        # Get company info
        company_info = ModelCompanyInfo(
            name=filing.company_name,
            cik=filing.cik,
            ticker=filing.ticker,
            fiscal_year_end=filing.fiscal_year_end
        )
        
        # Get all facts
        facts = [self._convert_fact_to_model(fact) for fact in filing.facts]
        
        # Get taxonomy elements
        taxonomy_elements = [self._convert_element_to_model(elem) for elem in filing.taxonomy_elements]
        
        return FilingData(
            company_info=company_info,
            filing_date=filing.filing_date,
            period_end_date=filing.period_end_date,
            form_type=filing.form_type,
            all_facts=facts,
            taxonomy_elements=taxonomy_elements
        )
    
    def _convert_fact_to_model(self, fact: Fact) -> FinancialFact:
        """Convert database Fact to FinancialFact model"""
        # Parse dimensions
        dimensions = {}
        if fact.dimensions:
            try:
                dimensions = json.loads(fact.dimensions)
            except json.JSONDecodeError:
                pass
        
        # Determine period type
        period_type = PeriodType.DURATION
        if fact.period_type == "instant":
            period_type = PeriodType.INSTANT
        
        return FinancialFact(
            concept=fact.concept,
            label=fact.label,
            value=fact.numeric_value if fact.numeric_value is not None else fact.value,
            unit=fact.unit,
            period=fact.period,
            period_type=period_type,
            context_id=fact.context_id,
            decimals=fact.decimals,
            dimensions=dimensions,
            period_start=fact.period_start,
            period_end=fact.period_end
        )
    
    def _convert_element_to_model(self, element: TaxonomyElement) -> ModelTaxonomyElement:
        """Convert database TaxonomyElement to model"""
        period_type = PeriodType.DURATION
        if element.period_type == "instant":
            period_type = PeriodType.INSTANT
        
        return ModelTaxonomyElement(
            name=element.name,
            type=element.type,
            substitution_group=element.substitution_group,
            period_type=period_type,
            balance=element.balance,
            abstract=element.abstract,
            nillable=element.nillable
        )