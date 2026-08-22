import enum
from typing import Tuple

class HealthState(str, enum.Enum):
    HEALTHY = "HEALTHY"
    SUSPICIOUS = "SUSPICIOUS"
    BROKEN = "BROKEN"
    UNKNOWN = "UNKNOWN"

class ScraperHealthService:
    @staticmethod
    def evaluate(http_status: int, current_jobs: int, previous_jobs: int = -1, has_active_rule: bool = False, rule_matched_elements: int = 0) -> Tuple[HealthState, str]:
        """
        Determines if the scraper needs healing.
        """
        if http_status and http_status >= 400:
            return HealthState.BROKEN, f"HTTP Error {http_status}"
            
        if current_jobs > 0:
            return HealthState.HEALTHY, "Successfully extracted jobs."
            
        # 0 jobs extracted
        if not has_active_rule:
            return HealthState.UNKNOWN, "No active rule and 0 jobs extracted."
            
        if rule_matched_elements == 0:
            # Active rule completely failed to find the listing selector
            return HealthState.BROKEN, "Active rule listing selector matched 0 elements."
            
        if previous_jobs > 0:
            return HealthState.SUSPICIOUS, f"Rule matched elements but extracted 0 jobs. Previous jobs: {previous_jobs}."
            
        return HealthState.UNKNOWN, "0 jobs extracted, but no historical baseline to compare."
