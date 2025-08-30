"""
XBRL Instance Document Parser

Parses XBRL instance documents to extract financial facts with their contexts,
periods, and dimensional information.
"""

import re
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from lxml import etree

from ..models import FinancialFact, PeriodType, CompanyInfo
from ..utils.logging import get_logger
from ..utils.exceptions import XBRLParsingError

logger = get_logger(__name__)


class InstanceParser:
    """
    Parser for XBRL instance documents
    """
    
    def __init__(self):
        self.namespaces: Dict[str, str] = {}
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.units: Dict[str, str] = {}
        self.facts: List[FinancialFact] = []
        self.company_info: Optional[CompanyInfo] = None
        
        # Common XBRL namespaces
        self.common_namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'xbrldi': 'http://xbrl.org/2006/xbrldi',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def parse_instance(self, instance_path: str) -> Tuple[List[FinancialFact], Optional[CompanyInfo]]:
        """
        Parse XBRL instance document
        
        Args:
            instance_path: Path to instance document
            
        Returns:
            Tuple of (facts list, company info)
            
        Raises:
            XBRLParsingError: If parsing fails
        """
        try:
            instance_file = Path(instance_path)
            if not instance_file.exists():
                raise XBRLParsingError(f"Instance file not found: {instance_path}")
            
            logger.info(f"Parsing instance document: {instance_path}")
            
            # Parse XML
            tree = etree.parse(str(instance_file))
            root = tree.getroot()
            
            # Extract namespaces
            self._extract_namespaces(root)
            
            # Parse contexts
            self._parse_contexts(root)
            
            # Parse units
            self._parse_units(root)
            
            # Parse facts
            self._parse_facts(root)
            
            # Extract company information
            self._extract_company_info(root)
            
            logger.info(f"Successfully parsed {len(self.facts)} facts from instance document")
            return self.facts, self.company_info
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"XML syntax error in instance document: {str(e)}",
                file_path=instance_path,
                line_number=getattr(e, 'lineno', None)
            )
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse instance document: {str(e)}",
                file_path=instance_path
            )
    
    def _extract_namespaces(self, root: etree.Element):
        """Extract namespace declarations"""
        self.namespaces = {}
        
        # Extract namespaces from root, handling None keys
        if root.nsmap:
            for prefix, uri in root.nsmap.items():
                if prefix is not None:  # Skip None prefix (default namespace)
                    self.namespaces[prefix] = uri
                else:
                    # Handle default namespace by assigning it a prefix
                    self.namespaces['default'] = uri
        
        # Add common namespaces if not present
        for prefix, uri in self.common_namespaces.items():
            if prefix not in self.namespaces:
                self.namespaces[prefix] = uri
        
        logger.debug(f"Extracted {len(self.namespaces)} namespaces")
    
    def _parse_contexts(self, root: etree.Element):
        """Parse XBRL contexts"""
        context_elements = root.xpath('.//xbrli:context', namespaces=self.namespaces)
        
        for context_elem in context_elements:
            context_id = context_elem.get('id')
            if not context_id:
                continue
            
            context_data = {
                'id': context_id,
                'entity': None,
                'period': None,
                'dimensions': {}
            }
            
            # Parse entity
            entity_elem = context_elem.xpath('.//xbrli:entity', namespaces=self.namespaces)
            if entity_elem:
                entity_data = self._parse_entity(entity_elem[0])
                context_data['entity'] = entity_data
            
            # Parse period
            period_elem = context_elem.xpath('.//xbrli:period', namespaces=self.namespaces)
            if period_elem:
                period_data = self._parse_period(period_elem[0])
                context_data['period'] = period_data
            
            # Parse scenario (dimensions)
            scenario_elem = context_elem.xpath('.//xbrli:scenario', namespaces=self.namespaces)
            if scenario_elem:
                dimensions = self._parse_dimensions(scenario_elem[0])
                context_data['dimensions'] = dimensions
            
            self.contexts[context_id] = context_data
        
        logger.debug(f"Parsed {len(self.contexts)} contexts")
    
    def _parse_entity(self, entity_elem: etree.Element) -> Dict[str, Any]:
        """Parse entity information"""
        entity_data = {}
        
        # Get identifier
        identifier_elem = entity_elem.xpath('.//xbrli:identifier', namespaces=self.namespaces)
        if identifier_elem:
            identifier = identifier_elem[0]
            entity_data['identifier'] = identifier.text
            entity_data['scheme'] = identifier.get('scheme')
        
        return entity_data
    
    def _parse_period(self, period_elem: etree.Element) -> Dict[str, Any]:
        """Parse period information"""
        period_data = {}
        
        # Check for instant period
        instant_elem = period_elem.xpath('.//xbrli:instant', namespaces=self.namespaces)
        if instant_elem:
            period_data['type'] = 'instant'
            period_data['instant'] = self._parse_date(instant_elem[0].text)
            return period_data
        
        # Check for duration period
        start_elem = period_elem.xpath('.//xbrli:startDate', namespaces=self.namespaces)
        end_elem = period_elem.xpath('.//xbrli:endDate', namespaces=self.namespaces)
        
        if start_elem and end_elem:
            period_data['type'] = 'duration'
            period_data['start_date'] = self._parse_date(start_elem[0].text)
            period_data['end_date'] = self._parse_date(end_elem[0].text)
        
        return period_data
    
    def _parse_dimensions(self, scenario_elem: etree.Element) -> Dict[str, str]:
        """Parse dimensional information from scenario"""
        dimensions = {}
        
        # Look for explicit members
        explicit_members = scenario_elem.xpath('.//xbrldi:explicitMember', namespaces=self.namespaces)
        for member in explicit_members:
            dimension = member.get('dimension')
            value = member.text
            if dimension and value:
                dimensions[dimension] = value
        
        # Look for typed members (less common)
        typed_members = scenario_elem.xpath('.//xbrldi:typedMember', namespaces=self.namespaces)
        for member in typed_members:
            dimension = member.get('dimension')
            if dimension:
                # Get the typed value (could be complex)
                value = etree.tostring(member, encoding='unicode', method='text').strip()
                dimensions[dimension] = value
        
        return dimensions
    
    def _parse_units(self, root: etree.Element):
        """Parse XBRL units"""
        unit_elements = root.xpath('.//xbrli:unit', namespaces=self.namespaces)
        
        for unit_elem in unit_elements:
            unit_id = unit_elem.get('id')
            if not unit_id:
                continue
            
            # Look for measure
            measure_elem = unit_elem.xpath('.//xbrli:measure', namespaces=self.namespaces)
            if measure_elem:
                measure = measure_elem[0].text
                self.units[unit_id] = measure
            else:
                # Handle divide units (ratios)
                numerator = unit_elem.xpath('.//xbrli:unitNumerator/xbrli:measure', namespaces=self.namespaces)
                denominator = unit_elem.xpath('.//xbrli:unitDenominator/xbrli:measure', namespaces=self.namespaces)
                
                if numerator and denominator:
                    unit_str = f"{numerator[0].text}/{denominator[0].text}"
                    self.units[unit_id] = unit_str
        
        logger.debug(f"Parsed {len(self.units)} units")
    
    def _parse_facts(self, root: etree.Element):
        """Parse financial facts from instance document"""
        facts = []
        
        # Get all elements that are not XBRL infrastructure elements
        for elem in root:
            if elem.tag.startswith('{http://www.xbrl.org/2003/instance}'):
                continue  # Skip XBRL infrastructure elements
            
            fact = self._parse_fact_element(elem)
            if fact:
                facts.append(fact)
        
        self.facts = facts
    
    def _parse_fact_element(self, elem: etree.Element) -> Optional[FinancialFact]:
        """Parse individual fact element"""
        try:
            # Get concept name
            concept = self._get_concept_name(elem.tag)
            if not concept:
                return None
            
            # Get value
            value = elem.text or ''
            if not value.strip():
                return None
            
            # Get attributes
            context_ref = elem.get('contextRef')
            unit_ref = elem.get('unitRef')
            decimals = elem.get('decimals')
            
            if not context_ref:
                return None
            
            # Get context information
            context = self.contexts.get(context_ref, {})
            
            # Determine period information
            period_info = context.get('period', {})
            period_type = PeriodType.INSTANT if period_info.get('type') == 'instant' else PeriodType.DURATION
            
            period_start = None
            period_end = None
            period_str = context_ref
            
            if period_type == PeriodType.INSTANT:
                period_end = period_info.get('instant')
                period_str = period_end.isoformat() if period_end else context_ref
            else:
                period_start = period_info.get('start_date')
                period_end = period_info.get('end_date')
                if period_start and period_end:
                    period_str = f"{period_start.isoformat()}_to_{period_end.isoformat()}"
            
            # Get unit
            unit = None
            if unit_ref:
                unit = self.units.get(unit_ref)
            
            # Parse decimals
            decimals_int = None
            if decimals and decimals != 'INF':
                try:
                    decimals_int = int(decimals)
                except ValueError:
                    pass
            
            # Parse value to appropriate type
            parsed_value = self._parse_value(value, unit)
            
            # Get dimensions
            dimensions = context.get('dimensions', {})
            
            # Create fact
            fact = FinancialFact(
                concept=concept,
                label=concept.split(':')[-1] if ':' in concept else concept,  # Default label
                value=parsed_value,
                unit=unit,
                period=period_str,
                period_type=period_type,
                context_id=context_ref,
                decimals=decimals_int,
                dimensions=dimensions,
                period_start=period_start,
                period_end=period_end
            )
            
            return fact
            
        except Exception as e:
            logger.warning(f"Failed to parse fact element {elem.tag}: {str(e)}")
            return None
    
    def _get_concept_name(self, tag: str) -> Optional[str]:
        """Extract concept name from XML tag"""
        if not tag:
            return None
        
        # Handle namespaced tags
        if tag.startswith('{'):
            # Extract namespace and local name
            match = re.match(r'\{([^}]+)\}(.+)', tag)
            if match:
                namespace_uri, local_name = match.groups()
                
                # Find namespace prefix
                prefix = None
                for p, uri in self.namespaces.items():
                    if uri == namespace_uri:
                        prefix = p
                        break
                
                if prefix:
                    return f"{prefix}:{local_name}"
                else:
                    return local_name
        
        return tag
    
    def _parse_value(self, value_str: str, unit: Optional[str]) -> Union[float, str, int]:
        """Parse value string to appropriate type"""
        value_str = value_str.strip()
        
        # Handle empty values
        if not value_str:
            return value_str
        
        # Try to parse as number
        try:
            # Remove common formatting
            clean_value = value_str.replace(',', '').replace('$', '').replace('%', '')
            
            # Try integer first
            if '.' not in clean_value and 'e' not in clean_value.lower():
                return int(clean_value)
            else:
                return float(clean_value)
                
        except ValueError:
            # Return as string if not numeric
            return value_str
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Handle common date formats
            if 'T' in date_str:
                # ISO datetime format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.date()
            else:
                # ISO date format
                return datetime.fromisoformat(date_str).date()
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    def _extract_company_info(self, root: etree.Element):
        """Extract company information from instance document"""
        try:
            company_info = CompanyInfo(name="", cik="")
            
            # Look for common company information elements
            company_name_concepts = [
                'dei:EntityRegistrantName',
                'dei:EntityCommonStockSharesOutstanding'
            ]
            
            cik_concepts = [
                'dei:EntityCentralIndexKey'
            ]
            
            ticker_concepts = [
                'dei:TradingSymbol'
            ]
            
            # Extract company name
            for concept in company_name_concepts:
                fact = self._find_fact_by_concept(concept)
                if fact and isinstance(fact.value, str):
                    company_info.name = fact.value
                    break
            
            # Extract CIK
            for concept in cik_concepts:
                fact = self._find_fact_by_concept(concept)
                if fact:
                    company_info.cik = str(fact.value)
                    break
            
            # Extract ticker
            for concept in ticker_concepts:
                fact = self._find_fact_by_concept(concept)
                if fact and isinstance(fact.value, str):
                    company_info.ticker = fact.value
                    break
            
            # Only set company_info if we found at least name or CIK
            if company_info.name or company_info.cik:
                self.company_info = company_info
            
        except Exception as e:
            logger.warning(f"Failed to extract company info: {str(e)}")
    
    def _find_fact_by_concept(self, concept: str) -> Optional[FinancialFact]:
        """Find fact by concept name"""
        for fact in self.facts:
            if fact.concept == concept or fact.concept.endswith(f":{concept.split(':')[-1]}"):
                return fact
        return None
    
    def get_facts_by_period(self, period_end: date) -> List[FinancialFact]:
        """Get facts for a specific period"""
        matching_facts = []
        
        for fact in self.facts:
            if fact.period_end == period_end:
                matching_facts.append(fact)
        
        return matching_facts
    
    def get_facts_by_concept_pattern(self, pattern: str) -> List[FinancialFact]:
        """Get facts matching a concept pattern"""
        pattern_lower = pattern.lower()
        matching_facts = []
        
        for fact in self.facts:
            if pattern_lower in fact.concept.lower():
                matching_facts.append(fact)
        
        return matching_facts