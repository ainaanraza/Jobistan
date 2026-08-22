import json
from google import genai
from core.config import settings
from core.extraction.models import ScraperRuleSchema
from bs4 import BeautifulSoup
import re

class ScraperHealingService:
    @staticmethod
    def _clean_html(html: str) -> str:
        """Removes scripts, styles, svgs, and huge footers to save LLM tokens."""
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer"]):
            tag.decompose()
            
        # Clean up empty attributes and class names if they're insanely long (obfuscated)
        for tag in soup.find_all(True):
            if tag.has_attr('class'):
                if isinstance(tag['class'], list) and len(" ".join(tag['class'])) > 100:
                    del tag['class']
                    
        text = str(soup)
        # Collapse multiple blank lines
        text = re.sub(r'\n\s*\n', '\n', text)
        return text[:50000] # Limit to ~50k chars

    @staticmethod
    def propose_rule(html: str, url: str) -> ScraperRuleSchema:
        """
        Calls Gemini to propose a new ScraperRuleSchema based on the broken HTML.
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing. Cannot perform self-healing.")
            
        cleaned_html = ScraperHealingService._clean_html(html)
        
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        prompt = (
            "You are a web extraction rule generator. You are NOT allowed to generate executable code.\n"
            "You must analyze the supplied HTML and propose declarative extraction rules to extract job listings.\n\n"
            f"The URL of the page is: {url}\n\n"
            "Identify:\n"
            "- job listing container (the wrapper around a single job)\n"
            "- title\n"
            "- company\n"
            "- location\n"
            "- application_url (the href to apply)\n\n"
            "Return JSON matching this exact schema:\n"
            "{\n"
            "  \"listing\": {\"strategy\": \"css\", \"selector\": \"...\"},\n"
            "  \"fields\": {\n"
            "    \"title\": {\"strategy\": \"css\", \"selector\": \"...\"},\n"
            "    \"company\": {\"strategy\": \"css\", \"selector\": \"...\"},\n"
            "    \"location\": {\"strategy\": \"css\", \"selector\": \"...\"},\n"
            "    \"application_url\": {\"strategy\": \"attribute\", \"selector\": \"...\", \"attribute\": \"href\"}\n"
            "  }\n"
            "}\n\n"
            "Prefer selectors that are specific, stable, and semantically meaningful (like '.job-card' or 'h2.title'). "
            "Do NOT invent job data. Only return extraction rules.\n\n"
            "HTML CONTENT:\n"
            f"{cleaned_html}"
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            parsed = json.loads(response_text.strip())
            return ScraperRuleSchema(**parsed)
        except Exception as e:
            raise ValueError(f"LLM returned invalid rule schema: {e}")
