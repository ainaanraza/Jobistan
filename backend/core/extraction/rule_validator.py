from typing import List, Dict, Any, Tuple
from core.ingestion.base import NormalizedJob

class RuleValidator:
    @staticmethod
    def validate_extracted_records(records: List[Dict[str, Any]], url: str) -> Tuple[bool, float, List[str]]:
        """
        Validates raw extracted records to ensure they are high-quality job listings.
        Returns: (is_valid, score, reasons)
        """
        if not records:
            return False, 0.0, ["No elements matched the selector."]
            
        total = len(records)
        if total > 200:
            return False, 0.0, [f"Too many elements matched ({total}). Likely matched generic UI components."]
            
        valid_titles = 0
        valid_urls = 0
        valid_companies = 0
        valid_locations = 0
        
        seen_urls = set()
        seen_titles = set()
        
        for r in records:
            title = r.get("title")
            app_url = r.get("application_url")
            company = r.get("company")
            location = r.get("location")
            
            if title and len(str(title).strip()) > 3:
                valid_titles += 1
                seen_titles.add(str(title).strip().lower())
                
            if app_url and len(str(app_url).strip()) > 5:
                valid_urls += 1
                seen_urls.add(str(app_url).strip())
                
            if company and len(str(company).strip()) > 1:
                valid_companies += 1
                
            if location and len(str(location).strip()) > 2:
                valid_locations += 1

        title_ratio = valid_titles / total
        url_ratio = valid_urls / total
        
        reasons = []
        score = 0.0
        
        if title_ratio < 0.5:
            reasons.append(f"Too few valid titles ({valid_titles}/{total}).")
        else:
            score += (title_ratio * 0.4)
            
        if url_ratio < 0.5:
            reasons.append(f"Too few valid application URLs ({valid_urls}/{total}).")
        else:
            score += (url_ratio * 0.4)
            
        # Company and location add bonus points up to 1.0
        company_ratio = valid_companies / total
        score += (company_ratio * 0.1)
        
        location_ratio = valid_locations / total
        score += (location_ratio * 0.1)
        
        # Check for massive duplication
        if total > 5:
            if len(seen_titles) == 1:
                score *= 0.5
                reasons.append("All jobs have the exact same title. Unlikely to be a real listing.")
            if len(seen_urls) == 1 and url_ratio > 0:
                score *= 0.5
                reasons.append("All jobs point to the exact same URL.")
                
        is_valid = score >= 0.75
        
        if is_valid:
            reasons.insert(0, "Passed validation.")
            
        return is_valid, round(score, 2), reasons
