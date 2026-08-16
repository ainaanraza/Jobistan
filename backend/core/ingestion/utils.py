import re
from typing import Dict, Any, Tuple, Optional
from core.ingestion.base import NormalizedJob

def parse_salary(text: str) -> Dict[str, Any]:
    """
    Parses a string like "70,000-1,20,000/Month" and returns:
    { "salary_min": 70000, "salary_max": 120000, "currency": "INR", "period": "MONTH" }
    """
    result = {
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "period": None
    }
    if not text:
        return result
        
    text_upper = text.upper()
    
    # Detect currency
    if "USD" in text_upper or "$" in text_upper:
        result["currency"] = "USD"
    elif "EUR" in text_upper or "€" in text_upper:
        result["currency"] = "EUR"
    elif "GBP" in text_upper or "£" in text_upper:
        result["currency"] = "GBP"
    else:
        # Default or fallback
        result["currency"] = "INR"
        
    # Detect period
    if "MONTH" in text_upper or "/MO" in text_upper:
        result["period"] = "MONTH"
    elif "YEAR" in text_upper or "/YR" in text_upper or "ANNUAL" in text_upper or "PA" in text_upper or "P.A" in text_upper:
        result["period"] = "YEAR"
    elif "HOUR" in text_upper or "/HR" in text_upper:
        result["period"] = "HOUR"
    elif "DAY" in text_upper:
        result["period"] = "DAY"
        
    # Extract numbers (remove commas)
    clean_text = text.replace(",", "")
    numbers = re.findall(r'\d+(?:\.\d+)?', clean_text)
    
    if len(numbers) >= 2:
        result["salary_min"] = float(numbers[0])
        result["salary_max"] = float(numbers[1])
    elif len(numbers) == 1:
        result["salary_min"] = float(numbers[0])
        result["salary_max"] = float(numbers[0])
        
    return result

def parse_location(text: str) -> Dict[str, Any]:
    """
    Extracts city, state, country, and remote/hybrid flags from location string.
    """
    result = {
        "city": None,
        "state": None,
        "country": None,
        "remote": False,
        "hybrid": False
    }
    if not text:
        return result
        
    text_lower = text.lower()
    
    if "remote" in text_lower or "telecommute" in text_lower or "anywhere" in text_lower:
        result["remote"] = True
    if "hybrid" in text_lower:
        result["hybrid"] = True
        
    # Simple split by comma for City, State, Country (Naive approach)
    parts = [p.strip() for p in text.split(",")]
    
    # Very basic heuristic:
    if len(parts) >= 3:
        result["city"] = parts[0]
        result["state"] = parts[1]
        result["country"] = parts[2]
    elif len(parts) == 2:
        result["city"] = parts[0]
        # Check if second part looks like a state or country
        if len(parts[1]) == 2 and parts[1].isupper():
            result["state"] = parts[1]
            result["country"] = "USA"
        else:
            result["country"] = parts[1]
    elif len(parts) == 1 and not result["remote"]:
        result["city"] = parts[0]
        
    return result

def validate_job(job: NormalizedJob) -> Tuple[str, float]:
    """
    Returns (validation_status, extraction_confidence).
    validation_status: VALID, WARNING, INVALID
    extraction_confidence: 0.0 to 1.0
    """
    score = 0.0
    status = "VALID"
    
    # Critical fields
    if not job.title or job.title == "Unknown Role" or len(job.title) < 2:
        return "INVALID", 0.0
    score += 0.4
        
    if not job.company or job.company == "Unknown Company" or len(job.company) < 2:
        return "INVALID", 0.0
    score += 0.2
        
    if not job.application_url or len(job.application_url) < 5:
        return "INVALID", 0.0
    score += 0.2
        
    # Non-critical fields
    if job.description and len(job.description) > 20:
        score += 0.1
    else:
        status = "WARNING"
        
    if job.location and job.location != "Unknown":
        score += 0.1
    else:
        status = "WARNING"
        
    return status, round(score, 2)
