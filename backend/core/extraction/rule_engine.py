from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from lxml import etree
import re
from urllib.parse import urljoin
from core.extraction.models import ScraperRuleSchema, FieldExtractionRule

class RuleEngine:
    @staticmethod
    def extract(html: str, url: str, rule: ScraperRuleSchema) -> List[Dict[str, Any]]:
        """
        Extracts structured data from HTML using the provided declarative rules.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # We also create an lxml tree for xpath support
        try:
            tree = etree.HTML(html)
        except Exception:
            tree = None

        listings = []
        if rule.listing.strategy == 'css':
            elements = soup.select(rule.listing.selector)
            for el in elements:
                extracted_data = RuleEngine._extract_fields(el, rule.fields, url, tree, el)
                if extracted_data:
                    listings.append(extracted_data)
        elif rule.listing.strategy == 'xpath' and tree is not None:
            elements = tree.xpath(rule.listing.selector)
            for el in elements:
                extracted_data = RuleEngine._extract_fields(None, rule.fields, url, tree, el)
                if extracted_data:
                    listings.append(extracted_data)
        
        return listings
        
    @staticmethod
    def _extract_fields(soup_el: Optional[BeautifulSoup], fields: Dict[str, FieldExtractionRule], base_url: str, tree, lxml_el) -> Dict[str, Any]:
        result = {}
        for field_name, field_rule in fields.items():
            val = None
            if field_rule.strategy == 'css' and soup_el:
                found = soup_el.select(field_rule.selector)
                if found:
                    target = found[0]
                    if field_rule.attribute:
                        val = target.get(field_rule.attribute)
                    else:
                        val = target.get_text(strip=True)
            elif field_rule.strategy == 'xpath' and lxml_el is not None:
                try:
                    found = lxml_el.xpath(field_rule.selector)
                    if found:
                        if isinstance(found[0], str):
                            val = found[0].strip()
                        else:
                            # It's an element
                            if field_rule.attribute:
                                val = found[0].get(field_rule.attribute)
                            else:
                                val = "".join(found[0].itertext()).strip()
                except Exception:
                    pass
            elif field_rule.strategy == 'regex' and soup_el:
                text = soup_el.get_text()
                match = re.search(field_rule.selector, text)
                if match:
                    val = match.group(1) if match.groups() else match.group(0)
            
            # Resolve relative URLs
            if val and field_name in ['application_url', 'company_url'] and field_rule.attribute in ['href', 'src']:
                val = urljoin(base_url, val)
                
            result[field_name] = val
            
        return result
