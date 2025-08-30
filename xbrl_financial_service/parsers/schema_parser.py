"""
XBRL Schema Parser

Parses XBRL taxonomy schema files (.xsd) to extract element definitions,
namespaces, and taxonomy structure.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from lxml import etree
from urllib.parse import urljoin, urlparse

from ..models import TaxonomyElement, PeriodType
from ..utils.logging import get_logger
from ..utils.exceptions import XBRLParsingError

logger = get_logger(__name__)


class SchemaParser:
    """
    Parser for XBRL taxonomy schema files
    """
    
    def __init__(self):
        self.namespaces: Dict[str, str] = {}
        self.elements: Dict[str, TaxonomyElement] = {}
        self.imports: List[str] = []
        self.linkbase_refs: List[Dict[str, str]] = []
        
        # Common XBRL namespaces
        self.common_namespaces = {
            'xs': 'http://www.w3.org/2001/XMLSchema',
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xbrldt': 'http://xbrl.org/2005/xbrldt',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def parse_schema(self, schema_path: str) -> Dict[str, TaxonomyElement]:
        """
        Parse XBRL schema file and extract taxonomy elements
        
        Args:
            schema_path: Path to the schema file
            
        Returns:
            Dictionary of element name to TaxonomyElement
            
        Raises:
            XBRLParsingError: If parsing fails
        """
        try:
            schema_file = Path(schema_path)
            if not schema_file.exists():
                raise XBRLParsingError(f"Schema file not found: {schema_path}")
            
            logger.info(f"Parsing schema file: {schema_path}")
            
            # Parse XML
            tree = etree.parse(str(schema_file))
            root = tree.getroot()
            
            # Extract namespaces
            self._extract_namespaces(root)
            
            # Extract imports
            self._extract_imports(root)
            
            # Extract linkbase references
            self._extract_linkbase_refs(root)
            
            # Extract element definitions
            self._extract_elements(root)
            
            logger.info(f"Successfully parsed {len(self.elements)} elements from schema")
            return self.elements
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"XML syntax error in schema file: {str(e)}",
                file_path=schema_path,
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse schema file: {str(e)}",
                file_path=schema_path
            )
    
    def _extract_namespaces(self, root: etree.Element):
        """Extract namespace declarations from schema root"""
        self.namespaces = dict(root.nsmap) if root.nsmap else {}
        
        # Add common namespaces if not present
        for prefix, uri in self.common_namespaces.items():
            if prefix not in self.namespaces:
                self.namespaces[prefix] = uri
        
        logger.debug(f"Extracted {len(self.namespaces)} namespaces")
    
    def _extract_imports(self, root: etree.Element):
        """Extract schema imports"""
        import_elements = root.xpath('.//xs:import', namespaces=self.namespaces)
        
        for import_elem in import_elements:
            namespace = import_elem.get('namespace')
            schema_location = import_elem.get('schemaLocation')
            
            if namespace and schema_location:
                self.imports.append({
                    'namespace': namespace,
                    'schemaLocation': schema_location
                })
        
        logger.debug(f"Found {len(self.imports)} schema imports")
    
    def _extract_linkbase_refs(self, root: etree.Element):
        """Extract linkbase references from schema annotations"""
        linkbase_refs = root.xpath(
            './/link:linkbaseRef',
            namespaces=self.namespaces
        )
        
        for ref in linkbase_refs:
            href = ref.get('{http://www.w3.org/1999/xlink}href')
            role = ref.get('{http://www.w3.org/1999/xlink}role')
            arcrole = ref.get('{http://www.w3.org/1999/xlink}arcrole')
            
            if href:
                self.linkbase_refs.append({
                    'href': href,
                    'role': role,
                    'arcrole': arcrole
                })
        
        logger.debug(f"Found {len(self.linkbase_refs)} linkbase references")
    
    def _extract_elements(self, root: etree.Element):
        """Extract element definitions from schema"""
        element_nodes = root.xpath('.//xs:element', namespaces=self.namespaces)
        
        for elem_node in element_nodes:
            element = self._parse_element_node(elem_node)
            if element:
                self.elements[element.name] = element
    
    def _parse_element_node(self, elem_node: etree.Element) -> Optional[TaxonomyElement]:
        """
        Parse individual element node
        
        Args:
            elem_node: XML element node
            
        Returns:
            TaxonomyElement or None if parsing fails
        """
        try:
            name = elem_node.get('name')
            if not name:
                return None
            
            # Get element attributes
            type_attr = elem_node.get('type', 'xs:string')
            substitution_group = elem_node.get('substitutionGroup', '')
            abstract = elem_node.get('abstract', 'false').lower() == 'true'
            nillable = elem_node.get('nillable', 'true').lower() == 'true'
            
            # Determine period type from substitution group
            period_type = self._determine_period_type(substitution_group)
            
            # Determine balance type
            balance = self._determine_balance_type(substitution_group)
            
            # Create full element name with namespace prefix
            target_namespace = elem_node.getroottree().getroot().get('targetNamespace')
            namespace_prefix = self._get_namespace_prefix(target_namespace)
            full_name = f"{namespace_prefix}:{name}" if namespace_prefix else name
            
            return TaxonomyElement(
                name=full_name,
                type=type_attr,
                substitution_group=substitution_group,
                period_type=period_type,
                balance=balance,
                abstract=abstract,
                nillable=nillable
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse element node: {str(e)}")
            return None
    
    def _determine_period_type(self, substitution_group: str) -> PeriodType:
        """
        Determine period type from substitution group
        
        Args:
            substitution_group: XBRL substitution group
            
        Returns:
            PeriodType enum value
        """
        if not substitution_group:
            return PeriodType.DURATION
        
        # Common patterns for instant vs duration
        instant_patterns = [
            'xbrli:item',
            'monetaryItemType',
            'sharesItemType',
            'percentItemType'
        ]
        
        duration_patterns = [
            'durationItemType',
            'stringItemType'
        ]
        
        substitution_lower = substitution_group.lower()
        
        # Check for instant patterns
        for pattern in instant_patterns:
            if pattern.lower() in substitution_lower:
                return PeriodType.INSTANT
        
        # Check for duration patterns  
        for pattern in duration_patterns:
            if pattern.lower() in substitution_lower:
                return PeriodType.DURATION
        
        # Default to duration
        return PeriodType.DURATION
    
    def _determine_balance_type(self, substitution_group: str) -> Optional[str]:
        """
        Determine balance type (debit/credit) from substitution group
        
        Args:
            substitution_group: XBRL substitution group
            
        Returns:
            'debit', 'credit', or None
        """
        if not substitution_group:
            return None
        
        substitution_lower = substitution_group.lower()
        
        # Common patterns for balance types
        if any(pattern in substitution_lower for pattern in ['asset', 'expense', 'loss']):
            return 'debit'
        elif any(pattern in substitution_lower for pattern in ['liability', 'equity', 'revenue', 'income']):
            return 'credit'
        
        return None
    
    def _get_namespace_prefix(self, namespace_uri: str) -> Optional[str]:
        """
        Get namespace prefix for a given URI
        
        Args:
            namespace_uri: Namespace URI
            
        Returns:
            Namespace prefix or None
        """
        for prefix, uri in self.namespaces.items():
            if uri == namespace_uri:
                return prefix
        return None
    
    def get_linkbase_files(self, schema_dir: Path) -> Dict[str, str]:
        """
        Get linkbase file paths referenced in the schema
        
        Args:
            schema_dir: Directory containing schema file
            
        Returns:
            Dictionary mapping linkbase type to file path
        """
        linkbase_files = {}
        
        for ref in self.linkbase_refs:
            href = ref.get('href')
            role = ref.get('role', '')
            
            if not href:
                continue
            
            # Determine linkbase type from role
            linkbase_type = self._determine_linkbase_type(role, href)
            
            # Resolve file path
            file_path = schema_dir / href
            if file_path.exists():
                linkbase_files[linkbase_type] = str(file_path)
        
        return linkbase_files
    
    def _determine_linkbase_type(self, role: str, href: str) -> str:
        """
        Determine linkbase type from role URI or filename
        
        Args:
            role: XBRL role URI
            href: File reference
            
        Returns:
            Linkbase type string
        """
        # Check role URI patterns
        if role:
            if 'calculationLinkbaseRef' in role:
                return 'calculation'
            elif 'presentationLinkbaseRef' in role:
                return 'presentation'
            elif 'labelLinkbaseRef' in role:
                return 'label'
            elif 'definitionLinkbaseRef' in role:
                return 'definition'
        
        # Check filename patterns
        href_lower = href.lower()
        if '_cal.xml' in href_lower:
            return 'calculation'
        elif '_pre.xml' in href_lower:
            return 'presentation'
        elif '_lab.xml' in href_lower:
            return 'label'
        elif '_def.xml' in href_lower:
            return 'definition'
        
        return 'unknown'
    
    def get_imported_schemas(self, schema_dir: Path) -> List[str]:
        """
        Get paths to imported schema files
        
        Args:
            schema_dir: Directory containing schema file
            
        Returns:
            List of imported schema file paths
        """
        imported_files = []
        
        for import_info in self.imports:
            schema_location = import_info.get('schemaLocation')
            if schema_location:
                # Handle both relative and absolute URLs
                if schema_location.startswith('http'):
                    # Skip remote schemas for now
                    continue
                
                file_path = schema_dir / schema_location
                if file_path.exists():
                    imported_files.append(str(file_path))
        
        return imported_files