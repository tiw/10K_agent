"""
Unified XBRL Parser

Main orchestrator for parsing complete XBRL filings including schema,
linkbases, and instance documents.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .models import (
    FilingData, FinancialFact, FinancialStatement, TaxonomyElement,
    CalculationRelationship, PresentationRelationship, CompanyInfo,
    StatementType
)
from .parsers import SchemaParser, LinkbaseParser, InstanceParser
from .config import Config
from .utils.logging import get_logger
from .utils.exceptions import XBRLParsingError, DataValidationError

logger = get_logger(__name__)


class XBRLParser:
    """
    Main XBRL parser that coordinates parsing of all XBRL file types
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Initialize parsers
        self.schema_parser = SchemaParser()
        self.linkbase_parser = LinkbaseParser()
        self.instance_parser = InstanceParser()
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        
        # Statement role mappings
        self.statement_roles = {
            'CONSOLIDATEDSTATEMENTSOFOPERATIONS': StatementType.INCOME_STATEMENT,
            'CONSOLIDATEDBALANCESHEETS': StatementType.BALANCE_SHEET,
            'CONSOLIDATEDSTATEMENTSOFCASHFLOWS': StatementType.CASH_FLOW_STATEMENT,
            'CONSOLIDATEDSTATEMENTSOFSHAREHOLDERSEQUITY': StatementType.SHAREHOLDERS_EQUITY,
            'CONSOLIDATEDSTATEMENTSOFCOMPREHENSIVEINCOME': StatementType.COMPREHENSIVE_INCOME
        }
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def _update_progress(self, message: str, progress: float):
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(message, progress)
        logger.info(f"Progress: {progress:.1%} - {message}")
    
    def parse_filing(self, file_paths: Dict[str, str]) -> FilingData:
        """
        Parse complete XBRL filing from file paths
        
        Args:
            file_paths: Dictionary mapping file types to paths:
                - 'schema': Path to .xsd file
                - 'calculation': Path to _cal.xml file (optional)
                - 'definition': Path to _def.xml file (optional)
                - 'label': Path to _lab.xml file (optional)
                - 'presentation': Path to _pre.xml file (optional)
                - 'instance': Path to instance document (required)
        
        Returns:
            FilingData object containing all parsed information
            
        Raises:
            XBRLParsingError: If parsing fails
            DataValidationError: If required files are missing
        """
        start_time = time.time()
        
        try:
            # Validate required files
            self._validate_file_paths(file_paths)
            
            self._update_progress("Starting XBRL parsing", 0.0)
            
            # Parse files in parallel where possible
            if self.config.enable_parallel_processing:
                filing_data = self._parse_filing_parallel(file_paths)
            else:
                filing_data = self._parse_filing_sequential(file_paths)
            
            # Build financial statements
            self._update_progress("Building financial statements", 0.8)
            self._build_financial_statements(filing_data)
            
            # Validate data
            self._update_progress("Validating data", 0.9)
            self._validate_filing_data(filing_data)
            
            elapsed_time = time.time() - start_time
            self._update_progress(f"Parsing completed in {elapsed_time:.2f}s", 1.0)
            
            logger.info(f"Successfully parsed XBRL filing with {len(filing_data.all_facts)} facts")
            return filing_data
            
        except Exception as e:
            if isinstance(e, (XBRLParsingError, DataValidationError)):
                raise
            else:
                raise XBRLParsingError(f"Unexpected error during parsing: {str(e)}")
    
    def _validate_file_paths(self, file_paths: Dict[str, str]):
        """Validate that required files exist"""
        required_files = ['instance']
        
        for file_type in required_files:
            if file_type not in file_paths:
                raise DataValidationError(f"Required file type '{file_type}' not provided")
            
            file_path = file_paths[file_type]
            if not os.path.exists(file_path):
                raise DataValidationError(f"File not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                raise DataValidationError(
                    f"File too large: {file_path} ({file_size} bytes > {self.config.max_file_size})"
                )
    
    def _parse_filing_parallel(self, file_paths: Dict[str, str]) -> FilingData:
        """Parse filing using parallel processing"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_worker_threads) as executor:
            # Submit parsing tasks
            future_to_type = {}
            
            # Parse schema
            if 'schema' in file_paths:
                future = executor.submit(self._parse_schema_safe, file_paths['schema'])
                future_to_type[future] = 'schema'
            
            # Parse linkbases
            for linkbase_type in ['calculation', 'definition', 'label', 'presentation']:
                if linkbase_type in file_paths:
                    future = executor.submit(
                        self._parse_linkbase_safe, 
                        file_paths[linkbase_type], 
                        linkbase_type
                    )
                    future_to_type[future] = linkbase_type
            
            # Parse instance (must be done after others for label resolution)
            instance_future = executor.submit(self._parse_instance_safe, file_paths['instance'])
            future_to_type[instance_future] = 'instance'
            
            # Collect results
            completed_count = 0
            total_tasks = len(future_to_type)
            
            for future in as_completed(future_to_type):
                file_type = future_to_type[future]
                try:
                    result = future.result()
                    results[file_type] = result
                    completed_count += 1
                    
                    progress = 0.1 + (completed_count / total_tasks) * 0.6
                    self._update_progress(f"Parsed {file_type}", progress)
                    
                except Exception as e:
                    logger.error(f"Failed to parse {file_type}: {str(e)}")
                    results[file_type] = None
        
        return self._combine_parsing_results(results)
    
    def _parse_filing_sequential(self, file_paths: Dict[str, str]) -> FilingData:
        """Parse filing sequentially"""
        results = {}
        
        # Parse schema
        if 'schema' in file_paths:
            self._update_progress("Parsing schema", 0.1)
            results['schema'] = self._parse_schema_safe(file_paths['schema'])
        
        # Parse linkbases
        linkbase_types = ['calculation', 'definition', 'label', 'presentation']
        for i, linkbase_type in enumerate(linkbase_types):
            if linkbase_type in file_paths:
                progress = 0.2 + (i / len(linkbase_types)) * 0.4
                self._update_progress(f"Parsing {linkbase_type} linkbase", progress)
                results[linkbase_type] = self._parse_linkbase_safe(
                    file_paths[linkbase_type], 
                    linkbase_type
                )
        
        # Parse instance
        self._update_progress("Parsing instance document", 0.7)
        results['instance'] = self._parse_instance_safe(file_paths['instance'])
        
        return self._combine_parsing_results(results)
    
    def _parse_schema_safe(self, schema_path: str) -> Optional[Dict[str, TaxonomyElement]]:
        """Safely parse schema with error handling"""
        try:
            return self.schema_parser.parse_schema(schema_path)
        except Exception as e:
            logger.error(f"Failed to parse schema: {str(e)}")
            return None
    
    def _parse_linkbase_safe(self, linkbase_path: str, linkbase_type: str) -> Optional[Any]:
        """Safely parse linkbase with error handling"""
        try:
            if linkbase_type == 'calculation':
                return self.linkbase_parser.parse_calculation_linkbase(linkbase_path)
            elif linkbase_type == 'presentation':
                return self.linkbase_parser.parse_presentation_linkbase(linkbase_path)
            elif linkbase_type == 'label':
                return self.linkbase_parser.parse_label_linkbase(linkbase_path)
            elif linkbase_type == 'definition':
                return self.linkbase_parser.parse_definition_linkbase(linkbase_path)
            else:
                logger.warning(f"Unknown linkbase type: {linkbase_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse {linkbase_type} linkbase: {str(e)}")
            return None
    
    def _parse_instance_safe(self, instance_path: str) -> Optional[tuple]:
        """Safely parse instance with error handling"""
        try:
            return self.instance_parser.parse_instance(instance_path)
        except Exception as e:
            logger.error(f"Failed to parse instance: {str(e)}")
            return None
    
    def _combine_parsing_results(self, results: Dict[str, Any]) -> FilingData:
        """Combine parsing results into FilingData object"""
        # Get instance results
        instance_result = results.get('instance')
        if not instance_result:
            raise XBRLParsingError("Failed to parse instance document")
        
        facts, company_info = instance_result
        
        # Default company info if not found
        if not company_info:
            company_info = CompanyInfo(name="Unknown Company", cik="0000000000")
        
        # Get taxonomy elements
        taxonomy_elements = []
        schema_result = results.get('schema')
        if schema_result:
            taxonomy_elements = list(schema_result.values())
        
        # Enhance facts with labels
        self._enhance_facts_with_labels(facts)
        
        # Determine filing dates
        filing_date = None
        period_end_date = None
        
        if facts:
            # Find the most recent period end date
            period_ends = [fact.period_end for fact in facts if fact.period_end]
            if period_ends:
                period_end_date = max(period_ends)
                filing_date = period_end_date  # Default to period end
        
        # Create filing data
        filing_data = FilingData(
            company_info=company_info,
            filing_date=filing_date or period_end_date,
            period_end_date=period_end_date,
            form_type="10-K",  # Default, could be enhanced
            all_facts=facts,
            taxonomy_elements=taxonomy_elements
        )
        
        return filing_data
    
    def _enhance_facts_with_labels(self, facts: List[FinancialFact]):
        """Enhance facts with human-readable labels from linkbase"""
        if not self.linkbase_parser.labels:
            return
        
        for fact in facts:
            # Try to get a better label
            label = self.linkbase_parser.get_concept_label(fact.concept)
            if label:
                fact.label = label
    
    def _build_financial_statements(self, filing_data: FilingData):
        """Build structured financial statements from facts"""
        # Group facts by statement type based on concept patterns
        statement_facts = self._classify_facts_by_statement(filing_data.all_facts)
        
        # Build individual statements
        for statement_type, facts in statement_facts.items():
            if not facts:
                continue
            
            # Get relevant calculations and presentations
            calculations = self._get_calculations_for_statement(statement_type)
            presentations = self._get_presentations_for_statement(statement_type)
            
            # Create financial statement
            statement = FinancialStatement(
                statement_type=statement_type,
                company_name=filing_data.company_info.name,
                period_end=filing_data.period_end_date,
                facts=facts,
                calculations=calculations,
                presentation_order=presentations
            )
            
            # Assign to filing data
            if statement_type == StatementType.INCOME_STATEMENT:
                filing_data.income_statement = statement
            elif statement_type == StatementType.BALANCE_SHEET:
                filing_data.balance_sheet = statement
            elif statement_type == StatementType.CASH_FLOW_STATEMENT:
                filing_data.cash_flow_statement = statement
            elif statement_type == StatementType.SHAREHOLDERS_EQUITY:
                filing_data.shareholders_equity = statement
            elif statement_type == StatementType.COMPREHENSIVE_INCOME:
                filing_data.comprehensive_income = statement
    
    def _classify_facts_by_statement(self, facts: List[FinancialFact]) -> Dict[StatementType, List[FinancialFact]]:
        """Classify facts by financial statement type"""
        statement_facts = {statement_type: [] for statement_type in StatementType}
        
        # Define concept patterns for each statement type
        patterns = {
            StatementType.INCOME_STATEMENT: [
                'revenue', 'income', 'expense', 'cost', 'profit', 'loss', 'earnings'
            ],
            StatementType.BALANCE_SHEET: [
                'asset', 'liability', 'equity', 'cash', 'receivable', 'payable', 'debt'
            ],
            StatementType.CASH_FLOW_STATEMENT: [
                'cashflow', 'cash', 'operating', 'investing', 'financing'
            ],
            StatementType.SHAREHOLDERS_EQUITY: [
                'equity', 'stock', 'shares', 'dividend', 'retained'
            ],
            StatementType.COMPREHENSIVE_INCOME: [
                'comprehensive', 'other'
            ]
        }
        
        for fact in facts:
            concept_lower = fact.concept.lower()
            label_lower = fact.label.lower()
            
            # Try to match to statement types
            matched = False
            for statement_type, keywords in patterns.items():
                if any(keyword in concept_lower or keyword in label_lower for keyword in keywords):
                    statement_facts[statement_type].append(fact)
                    matched = True
                    break
            
            # Default to income statement if no match
            if not matched:
                statement_facts[StatementType.INCOME_STATEMENT].append(fact)
        
        return statement_facts
    
    def _get_calculations_for_statement(self, statement_type: StatementType) -> List[CalculationRelationship]:
        """Get calculation relationships for a statement type"""
        # This would be enhanced with role-based filtering
        return self.linkbase_parser.calculations
    
    def _get_presentations_for_statement(self, statement_type: StatementType) -> List[PresentationRelationship]:
        """Get presentation relationships for a statement type"""
        # This would be enhanced with role-based filtering
        return self.linkbase_parser.presentations
    
    def _validate_filing_data(self, filing_data: FilingData):
        """Validate parsed filing data"""
        if not filing_data.all_facts:
            raise DataValidationError("No facts found in filing")
        
        if not filing_data.company_info.name:
            logger.warning("Company name not found")
        
        if not filing_data.period_end_date:
            logger.warning("Period end date not found")
        
        # Validate calculation relationships if strict validation is enabled
        if self.config.strict_validation:
            self._validate_calculations(filing_data)
    
    def _validate_calculations(self, filing_data: FilingData):
        """Validate calculation relationships against facts"""
        # This would implement calculation validation logic
        # For now, just log a message
        logger.info("Calculation validation would be performed here")
    
    def parse_filing_from_directory(self, directory_path: str) -> FilingData:
        """
        Parse XBRL filing from a directory containing all files
        
        Args:
            directory_path: Path to directory containing XBRL files
            
        Returns:
            FilingData object
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise XBRLParsingError(f"Directory not found: {directory_path}")
        
        # Auto-detect file types
        file_paths = self._auto_detect_files(directory)
        
        return self.parse_filing(file_paths)
    
    def _auto_detect_files(self, directory: Path) -> Dict[str, str]:
        """Auto-detect XBRL files in directory"""
        file_paths = {}
        
        for file_path in directory.glob("*"):
            if not file_path.is_file():
                continue
            
            filename = file_path.name.lower()
            
            if filename.endswith('.xsd'):
                file_paths['schema'] = str(file_path)
            elif filename.endswith('_cal.xml'):
                file_paths['calculation'] = str(file_path)
            elif filename.endswith('_def.xml'):
                file_paths['definition'] = str(file_path)
            elif filename.endswith('_lab.xml'):
                file_paths['label'] = str(file_path)
            elif filename.endswith('_pre.xml'):
                file_paths['presentation'] = str(file_path)
            elif filename.endswith('_htm.xml') or filename.endswith('.xml'):
                # Assume instance document
                if 'instance' not in file_paths:
                    file_paths['instance'] = str(file_path)
        
        return file_paths