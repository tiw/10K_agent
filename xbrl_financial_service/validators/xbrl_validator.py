"""
XBRL file validation module
Validates XML structure, schema compliance, and required elements
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from lxml import etree

from ..utils.exceptions import XBRLParsingError, DataValidationError
from ..models import FilingData


logger = logging.getLogger(__name__)


class XBRLValidator:
    """Validates XBRL files for structure, schema compliance, and required elements"""
    
    # Required XBRL file types for a complete filing
    REQUIRED_FILE_TYPES = {
        'schema': '.xsd',
        'calculation': '_cal.xml',
        'definition': '_def.xml', 
        'label': '_lab.xml',
        'presentation': '_pre.xml',
        'instance': '_htm.xml'
    }
    
    # Common XBRL namespaces
    XBRL_NAMESPACES = {
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xbrldt': 'http://xbrl.org/2005/xbrldt',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xs': 'http://www.w3.org/2001/XMLSchema'
    }
    
    def __init__(self):
        self.validation_errors: List[Dict] = []
        self.validation_warnings: List[Dict] = []
    
    def validate_filing_completeness(self, file_paths: Dict[str, str]) -> bool:
        """
        Validate that all required XBRL files are present
        
        Args:
            file_paths: Dictionary mapping file types to file paths
            
        Returns:
            bool: True if all required files are present
            
        Raises:
            DataValidationError: If required files are missing
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        missing_files = []
        invalid_files = []
        
        for file_type, expected_suffix in self.REQUIRED_FILE_TYPES.items():
            if file_type not in file_paths:
                missing_files.append(file_type)
                continue
                
            file_path = file_paths[file_type]
            
            # Check if file exists
            if not os.path.exists(file_path):
                invalid_files.append(f"{file_type}: {file_path} (file not found)")
                continue
                
            # Check file extension
            if not file_path.endswith(expected_suffix):
                self.validation_warnings.append({
                    "type": "file_extension",
                    "message": f"{file_type} file doesn't have expected suffix {expected_suffix}",
                    "file": file_path
                })
        
        if missing_files:
            raise DataValidationError(
                f"Missing required XBRL files: {', '.join(missing_files)}",
                validation_type="file_completeness",
                details={"missing_files": missing_files},
                suggestions=[
                    "Ensure all XBRL filing components are downloaded",
                    "Check file naming conventions",
                    "Verify filing package completeness"
                ]
            )
        
        if invalid_files:
            raise DataValidationError(
                f"Invalid or missing files: {'; '.join(invalid_files)}",
                validation_type="file_accessibility",
                details={"invalid_files": invalid_files},
                suggestions=[
                    "Check file paths and permissions",
                    "Verify files are not corrupted",
                    "Ensure proper file download"
                ]
            )
        
        return True
    
    def validate_xml_structure(self, file_path: str) -> bool:
        """
        Validate XML structure and well-formedness
        
        Args:
            file_path: Path to XML file to validate
            
        Returns:
            bool: True if XML is well-formed
            
        Raises:
            XBRLParsingError: If XML structure is invalid
        """
        try:
            # Parse with lxml for better error reporting
            with open(file_path, 'rb') as f:
                parser = etree.XMLParser(recover=False)
                etree.parse(f, parser)
            
            logger.debug(f"XML structure validation passed for {file_path}")
            return True
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"Invalid XML structure in {file_path}: {str(e)}",
                file_path=file_path,
                line_number=e.lineno if hasattr(e, 'lineno') else None,
                details={"xml_error": str(e)},
                suggestions=[
                    "Check XML syntax and structure",
                    "Verify file encoding (should be UTF-8)",
                    "Ensure all XML tags are properly closed",
                    "Check for invalid characters in XML content"
                ]
            )
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse XML file {file_path}: {str(e)}",
                file_path=file_path,
                details={"error": str(e)},
                suggestions=[
                    "Check file accessibility and permissions",
                    "Verify file is not corrupted",
                    "Ensure file is a valid XML document"
                ]
            )
    
    def validate_xbrl_namespaces(self, file_path: str) -> bool:
        """
        Validate that required XBRL namespaces are declared
        
        Args:
            file_path: Path to XBRL file
            
        Returns:
            bool: True if required namespaces are present
            
        Raises:
            DataValidationError: If required namespaces are missing
        """
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Get all namespace declarations
            declared_namespaces = root.nsmap or {}
            
            # Check for required XBRL namespaces based on file type
            required_namespaces = self._get_required_namespaces(file_path)
            missing_namespaces = []
            
            for prefix, uri in required_namespaces.items():
                if prefix not in declared_namespaces:
                    # Check if namespace is declared with different prefix
                    found_uri = False
                    for decl_prefix, decl_uri in declared_namespaces.items():
                        if decl_uri == uri:
                            found_uri = True
                            break
                    
                    if not found_uri:
                        missing_namespaces.append(f"{prefix} ({uri})")
                elif declared_namespaces[prefix] != uri:
                    self.validation_warnings.append({
                        "type": "namespace_mismatch",
                        "message": f"Namespace {prefix} has unexpected URI",
                        "expected": uri,
                        "actual": declared_namespaces[prefix],
                        "file": file_path
                    })
            
            if missing_namespaces:
                raise DataValidationError(
                    f"Missing required XBRL namespaces in {file_path}: {', '.join(missing_namespaces)}",
                    validation_type="namespace_validation",
                    details={
                        "missing_namespaces": missing_namespaces,
                        "declared_namespaces": declared_namespaces
                    },
                    suggestions=[
                        "Check XBRL file format compliance",
                        "Verify namespace declarations in root element",
                        "Ensure file follows XBRL specification"
                    ]
                )
            
            return True
            
        except etree.XMLSyntaxError as e:
            # Re-raise as parsing error since XML structure is invalid
            raise XBRLParsingError(
                f"Cannot validate namespaces due to XML syntax error in {file_path}",
                file_path=file_path,
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )
    
    def validate_required_elements(self, file_path: str, file_type: str) -> bool:
        """
        Validate that required XBRL elements are present
        
        Args:
            file_path: Path to XBRL file
            file_type: Type of XBRL file (schema, instance, etc.)
            
        Returns:
            bool: True if required elements are present
            
        Raises:
            DataValidationError: If required elements are missing
        """
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            required_elements = self._get_required_elements(file_type)
            missing_elements = []
            
            for element_path in required_elements:
                elements = root.xpath(element_path, namespaces=self.XBRL_NAMESPACES)
                if not elements:
                    missing_elements.append(element_path)
            
            if missing_elements:
                raise DataValidationError(
                    f"Missing required elements in {file_type} file {file_path}",
                    validation_type="required_elements",
                    details={
                        "missing_elements": missing_elements,
                        "file_type": file_type
                    },
                    suggestions=[
                        f"Check {file_type} file format compliance",
                        "Verify file contains all required XBRL elements",
                        "Ensure file follows XBRL taxonomy structure"
                    ]
                )
            
            return True
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"Cannot validate elements due to XML syntax error in {file_path}",
                file_path=file_path,
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )
    
    def validate_data_types(self, file_path: str) -> bool:
        """
        Validate data types and formats in XBRL instance documents
        
        Args:
            file_path: Path to XBRL instance file
            
        Returns:
            bool: True if data types are valid
            
        Raises:
            DataValidationError: If data type validation fails
        """
        if not file_path.endswith('_htm.xml'):
            # Only validate instance documents
            return True
        
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Find all fact elements (elements with contextRef attribute)
            facts = root.xpath(".//*[@contextRef]", namespaces=self.XBRL_NAMESPACES)
            
            validation_errors = []
            
            for fact in facts:
                try:
                    self._validate_fact_data_type(fact)
                except DataValidationError as e:
                    validation_errors.append({
                        "element": fact.tag,
                        "context": fact.get('contextRef'),
                        "value": fact.text,
                        "error": str(e)
                    })
            
            if validation_errors:
                raise DataValidationError(
                    f"Data type validation failed for {len(validation_errors)} facts in {file_path}",
                    validation_type="data_types",
                    details={"validation_errors": validation_errors[:10]},  # Limit to first 10
                    suggestions=[
                        "Check numeric values for proper formatting",
                        "Verify date formats (YYYY-MM-DD)",
                        "Ensure monetary values are numeric",
                        "Check for invalid characters in data"
                    ]
                )
            
            return True
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"Cannot validate data types due to XML syntax error in {file_path}",
                file_path=file_path,
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )
    
    def get_validation_report(self) -> Dict:
        """
        Get comprehensive validation report
        
        Returns:
            Dict: Validation report with errors and warnings
        """
        return {
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "error_count": len(self.validation_errors),
            "warning_count": len(self.validation_warnings),
            "is_valid": len(self.validation_errors) == 0
        }
    
    def _get_required_namespaces(self, file_path: str) -> Dict[str, str]:
        """Get required namespaces based on file type"""
        base_namespaces = {}
        
        if file_path.endswith('.xsd'):
            # Schema files typically have xs namespace
            base_namespaces.update({
                'xs': self.XBRL_NAMESPACES['xs']
            })
        elif file_path.endswith('_htm.xml'):
            # Instance documents need xbrli and xsi
            base_namespaces.update({
                'xbrli': self.XBRL_NAMESPACES['xbrli'],
                'xsi': self.XBRL_NAMESPACES['xsi']
            })
        elif any(file_path.endswith(suffix) for suffix in ['_cal.xml', '_def.xml', '_lab.xml', '_pre.xml']):
            # Linkbase files need link and xlink
            base_namespaces.update({
                'link': self.XBRL_NAMESPACES['link'],
                'xlink': self.XBRL_NAMESPACES['xlink']
            })
        
        return base_namespaces
    
    def _get_required_elements(self, file_type: str) -> List[str]:
        """Get required XPath expressions for elements based on file type"""
        if file_type == 'schema':
            return [
                "//xs:schema",
                "//xs:element"
            ]
        elif file_type == 'instance':
            return [
                "//xbrli:xbrl",
                "//xbrli:context"
            ]
        elif file_type in ['calculation', 'definition', 'label', 'presentation']:
            return [
                "//link:linkbase"
            ]
        
        return []
    
    def _validate_fact_data_type(self, fact_element) -> None:
        """Validate individual fact data type"""
        value = fact_element.text
        if not value:
            return  # Empty values are allowed
        
        value = value.strip()
        if not value:
            return
        
        # Get element name to infer expected data type
        element_name = fact_element.tag.split('}')[-1] if '}' in fact_element.tag else fact_element.tag
        
        # Only validate clearly numeric fields to avoid false positives
        # Many XBRL elements contain text, identifiers, or mixed content
        
        # Check for clearly monetary values (with units like USD)
        unit_ref = fact_element.get('unitRef', '')
        if 'usd' in unit_ref.lower() or any(keyword in element_name.lower() for keyword in ['amount', 'value']) and unit_ref:
            # This is likely a monetary value
            try:
                # Allow negative values and various formats
                cleaned_value = value.replace(',', '').replace('(', '-').replace(')', '')
                float(cleaned_value)
            except ValueError:
                # Only raise error for clearly monetary fields that can't be parsed
                if 'usd' in unit_ref.lower():
                    raise DataValidationError(
                        f"Invalid numeric value for monetary element {element_name}: {value}",
                        validation_type="data_type_monetary"
                    )
        
        # Validate dates only if they look like dates
        elif ('date' in element_name.lower() and 
              len(value) >= 8 and 
              '-' in value and 
              not any(char.isalpha() for char in value)):
            # Basic date format validation for date-like fields
            if not (len(value) == 10 and value.count('-') == 2):
                # Allow partial dates like "--09-28"
                if not value.startswith('--'):
                    raise DataValidationError(
                        f"Invalid date format for element {element_name}: {value}",
                        validation_type="data_type_date"
                    )
        
        # Skip validation for text fields, identifiers, and other non-numeric data
        # This includes entity numbers, phone numbers, addresses, etc.