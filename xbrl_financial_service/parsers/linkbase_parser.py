"""
XBRL Linkbase Parser

Parses XBRL linkbase files to extract relationships between concepts:
- Calculation linkbase (_cal.xml): calculation relationships
- Definition linkbase (_def.xml): dimensional relationships  
- Label linkbase (_lab.xml): human-readable labels
- Presentation linkbase (_pre.xml): presentation hierarchy
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from lxml import etree
from urllib.parse import urlparse

from ..models import CalculationRelationship, PresentationRelationship
from ..utils.logging import get_logger
from ..utils.exceptions import XBRLParsingError

logger = get_logger(__name__)


class LinkbaseParser:
    """
    Parser for XBRL linkbase files
    """
    
    def __init__(self):
        self.namespaces = {
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink',
            'xbrldt': 'http://xbrl.org/2005/xbrldt',
            'xs': 'http://www.w3.org/2001/XMLSchema'
        }
        
        # Store parsed data
        self.calculations: List[CalculationRelationship] = []
        self.presentations: List[PresentationRelationship] = []
        self.labels: Dict[str, Dict[str, str]] = {}  # concept -> {role: label}
        self.definitions: List[Dict[str, Any]] = []
    
    def parse_calculation_linkbase(self, linkbase_path: str) -> List[CalculationRelationship]:
        """
        Parse calculation linkbase file
        
        Args:
            linkbase_path: Path to calculation linkbase file
            
        Returns:
            List of CalculationRelationship objects
            
        Raises:
            XBRLParsingError: If parsing fails
        """
        try:
            logger.info(f"Parsing calculation linkbase: {linkbase_path}")
            
            tree = etree.parse(linkbase_path)
            root = tree.getroot()
            
            # Update namespaces from document
            if root.nsmap:
                self.namespaces.update(root.nsmap)
            
            calculations = []
            
            # Find all calculation links
            calc_links = root.xpath('.//link:calculationLink', namespaces=self.namespaces)
            
            for calc_link in calc_links:
                role = calc_link.get('{http://www.w3.org/1999/xlink}role')
                calculations.extend(self._parse_calculation_link(calc_link, role))
            
            logger.info(f"Parsed {len(calculations)} calculation relationships")
            self.calculations = calculations
            return calculations
            
        except etree.XMLSyntaxError as e:
            raise XBRLParsingError(
                f"XML syntax error in calculation linkbase: {str(e)}",
                file_path=linkbase_path,
                line_number=getattr(e, 'lineno', None)
            )
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse calculation linkbase: {str(e)}",
                file_path=linkbase_path
            )
    
    def parse_presentation_linkbase(self, linkbase_path: str) -> List[PresentationRelationship]:
        """
        Parse presentation linkbase file
        
        Args:
            linkbase_path: Path to presentation linkbase file
            
        Returns:
            List of PresentationRelationship objects
        """
        try:
            logger.info(f"Parsing presentation linkbase: {linkbase_path}")
            
            tree = etree.parse(linkbase_path)
            root = tree.getroot()
            
            if root.nsmap:
                self.namespaces.update(root.nsmap)
            
            presentations = []
            
            # Find all presentation links
            pres_links = root.xpath('.//link:presentationLink', namespaces=self.namespaces)
            
            for pres_link in pres_links:
                role = pres_link.get('{http://www.w3.org/1999/xlink}role')
                presentations.extend(self._parse_presentation_link(pres_link, role))
            
            logger.info(f"Parsed {len(presentations)} presentation relationships")
            self.presentations = presentations
            return presentations
            
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse presentation linkbase: {str(e)}",
                file_path=linkbase_path
            )
    
    def parse_label_linkbase(self, linkbase_path: str) -> Dict[str, Dict[str, str]]:
        """
        Parse label linkbase file
        
        Args:
            linkbase_path: Path to label linkbase file
            
        Returns:
            Dictionary mapping concept to labels by role
        """
        try:
            logger.info(f"Parsing label linkbase: {linkbase_path}")
            
            tree = etree.parse(linkbase_path)
            root = tree.getroot()
            
            if root.nsmap:
                self.namespaces.update(root.nsmap)
            
            labels = {}
            
            # Find all label links
            label_links = root.xpath('.//link:labelLink', namespaces=self.namespaces)
            
            for label_link in label_links:
                labels.update(self._parse_label_link(label_link))
            
            logger.info(f"Parsed labels for {len(labels)} concepts")
            self.labels = labels
            return labels
            
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse label linkbase: {str(e)}",
                file_path=linkbase_path
            )
    
    def parse_definition_linkbase(self, linkbase_path: str) -> List[Dict[str, Any]]:
        """
        Parse definition linkbase file
        
        Args:
            linkbase_path: Path to definition linkbase file
            
        Returns:
            List of definition relationships
        """
        try:
            logger.info(f"Parsing definition linkbase: {linkbase_path}")
            
            tree = etree.parse(linkbase_path)
            root = tree.getroot()
            
            if root.nsmap:
                self.namespaces.update(root.nsmap)
            
            definitions = []
            
            # Find all definition links
            def_links = root.xpath('.//link:definitionLink', namespaces=self.namespaces)
            
            for def_link in def_links:
                role = def_link.get('{http://www.w3.org/1999/xlink}role')
                definitions.extend(self._parse_definition_link(def_link, role))
            
            logger.info(f"Parsed {len(definitions)} definition relationships")
            self.definitions = definitions
            return definitions
            
        except Exception as e:
            raise XBRLParsingError(
                f"Failed to parse definition linkbase: {str(e)}",
                file_path=linkbase_path
            )
    
    def _parse_calculation_link(self, calc_link: etree.Element, role: Optional[str]) -> List[CalculationRelationship]:
        """Parse individual calculation link"""
        calculations = []
        
        # Get all locators (concept references)
        locators = {}
        for loc in calc_link.xpath('.//link:loc', namespaces=self.namespaces):
            label = loc.get('{http://www.w3.org/1999/xlink}label')
            href = loc.get('{http://www.w3.org/1999/xlink}href')
            if label and href:
                # Extract concept name from href (after #)
                concept = href.split('#')[-1] if '#' in href else href
                locators[label] = concept
        
        # Get all calculation arcs
        for arc in calc_link.xpath('.//link:calculationArc', namespaces=self.namespaces):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to')
            weight = float(arc.get('weight', '1.0'))
            order = int(arc.get('order', '0'))
            
            if from_label in locators and to_label in locators:
                parent_concept = locators[from_label]
                child_concept = locators[to_label]
                
                calculations.append(CalculationRelationship(
                    parent=parent_concept,
                    child=child_concept,
                    weight=weight,
                    order=order,
                    role=role
                ))
        
        return calculations
    
    def _parse_presentation_link(self, pres_link: etree.Element, role: Optional[str]) -> List[PresentationRelationship]:
        """Parse individual presentation link"""
        presentations = []
        
        # Get all locators
        locators = {}
        for loc in pres_link.xpath('.//link:loc', namespaces=self.namespaces):
            label = loc.get('{http://www.w3.org/1999/xlink}label')
            href = loc.get('{http://www.w3.org/1999/xlink}href')
            if label and href:
                concept = href.split('#')[-1] if '#' in href else href
                locators[label] = concept
        
        # Get all presentation arcs
        for arc in pres_link.xpath('.//link:presentationArc', namespaces=self.namespaces):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to')
            order = int(arc.get('order', '0'))
            preferred_label = arc.get('preferredLabel')
            
            if from_label in locators and to_label in locators:
                parent_concept = locators[from_label]
                child_concept = locators[to_label]
                
                presentations.append(PresentationRelationship(
                    parent=parent_concept,
                    child=child_concept,
                    order=order,
                    preferred_label=preferred_label,
                    role=role
                ))
        
        return presentations
    
    def _parse_label_link(self, label_link: etree.Element) -> Dict[str, Dict[str, str]]:
        """Parse individual label link"""
        labels = {}
        
        # Get all locators
        locators = {}
        for loc in label_link.xpath('.//link:loc', namespaces=self.namespaces):
            label = loc.get('{http://www.w3.org/1999/xlink}label')
            href = loc.get('{http://www.w3.org/1999/xlink}href')
            if label and href:
                concept = href.split('#')[-1] if '#' in href else href
                locators[label] = concept
        
        # Get all label resources
        label_resources = {}
        for label_elem in label_link.xpath('.//link:label', namespaces=self.namespaces):
            label = label_elem.get('{http://www.w3.org/1999/xlink}label')
            role = label_elem.get('{http://www.w3.org/1999/xlink}role')
            text = label_elem.text or ''
            
            if label:
                label_resources[label] = {
                    'text': text.strip(),
                    'role': role
                }
        
        # Connect locators to labels via labelArcs
        for arc in label_link.xpath('.//link:labelArc', namespaces=self.namespaces):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to')
            
            if from_label in locators and to_label in label_resources:
                concept = locators[from_label]
                label_info = label_resources[to_label]
                
                if concept not in labels:
                    labels[concept] = {}
                
                role = label_info['role'] or 'standard'
                labels[concept][role] = label_info['text']
        
        return labels
    
    def _parse_definition_link(self, def_link: etree.Element, role: Optional[str]) -> List[Dict[str, Any]]:
        """Parse individual definition link"""
        definitions = []
        
        # Get all locators
        locators = {}
        for loc in def_link.xpath('.//link:loc', namespaces=self.namespaces):
            label = loc.get('{http://www.w3.org/1999/xlink}label')
            href = loc.get('{http://www.w3.org/1999/xlink}href')
            if label and href:
                concept = href.split('#')[-1] if '#' in href else href
                locators[label] = concept
        
        # Get all definition arcs
        for arc in def_link.xpath('.//link:definitionArc', namespaces=self.namespaces):
            from_label = arc.get('{http://www.w3.org/1999/xlink}from')
            to_label = arc.get('{http://www.w3.org/1999/xlink}to')
            arcrole = arc.get('{http://www.w3.org/1999/xlink}arcrole')
            order = int(arc.get('order', '0'))
            
            # Additional attributes for dimensional relationships
            closed = arc.get('{http://xbrl.org/2005/xbrldt}closed')
            context_element = arc.get('{http://xbrl.org/2005/xbrldt}contextElement')
            
            if from_label in locators and to_label in locators:
                definitions.append({
                    'from_concept': locators[from_label],
                    'to_concept': locators[to_label],
                    'arcrole': arcrole,
                    'order': order,
                    'role': role,
                    'closed': closed,
                    'context_element': context_element
                })
        
        return definitions
    
    def get_concept_label(self, concept: str, role: str = 'standard') -> Optional[str]:
        """
        Get label for a concept
        
        Args:
            concept: Concept name
            role: Label role (default: 'standard')
            
        Returns:
            Label text or None if not found
        """
        concept_labels = self.labels.get(concept, {})
        
        # Try exact role match first
        if role in concept_labels:
            return concept_labels[role]
        
        # Try standard label
        if 'standard' in concept_labels:
            return concept_labels['standard']
        
        # Try any available label
        if concept_labels:
            return next(iter(concept_labels.values()))
        
        return None
    
    def get_calculation_children(self, parent_concept: str, role: Optional[str] = None) -> List[Tuple[str, float, int]]:
        """
        Get calculation children for a parent concept
        
        Args:
            parent_concept: Parent concept name
            role: Optional role filter
            
        Returns:
            List of (child_concept, weight, order) tuples
        """
        children = []
        
        for calc in self.calculations:
            if calc.parent == parent_concept:
                if role is None or calc.role == role:
                    children.append((calc.child, calc.weight, calc.order))
        
        # Sort by order
        children.sort(key=lambda x: x[2])
        return children
    
    def get_presentation_children(self, parent_concept: str, role: Optional[str] = None) -> List[Tuple[str, int, Optional[str]]]:
        """
        Get presentation children for a parent concept
        
        Args:
            parent_concept: Parent concept name
            role: Optional role filter
            
        Returns:
            List of (child_concept, order, preferred_label) tuples
        """
        children = []
        
        for pres in self.presentations:
            if pres.parent == parent_concept:
                if role is None or pres.role == role:
                    children.append((pres.child, pres.order, pres.preferred_label))
        
        # Sort by order
        children.sort(key=lambda x: x[1])
        return children