from typing import Optional, Dict
from pydantic import BaseModel, Field

class FieldExtractionRule(BaseModel):
    strategy: str = Field(description="The extraction strategy: 'css', 'xpath', 'attribute', 'text', 'regex'")
    selector: str = Field(description="The selector or pattern for the strategy.")
    attribute: Optional[str] = Field(None, description="The attribute to extract if strategy is 'attribute'. Example: 'href'.")

class ScraperRuleSchema(BaseModel):
    listing: FieldExtractionRule = Field(description="The rule to find individual job cards/containers on the page.")
    fields: Dict[str, FieldExtractionRule] = Field(description="Rules to extract specific fields from within each job card container.")
    pagination: Optional[FieldExtractionRule] = Field(None, description="Rule to find the 'next page' link, if applicable.")
